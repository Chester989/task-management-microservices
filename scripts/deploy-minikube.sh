#!/bin/bash
set -e

if [ ! -f kubernetes/segredos.yaml ]; then
    echo "Falta kubernetes/segredos.yaml. Copia kubernetes/segredos.example.yaml e substitui os valores REPLACE_ME."
    exit 1
fi

echo "============================================"
echo "  Deploy do Sistema de Gestao de Tarefas"
echo "  Minikube + Kubernetes"
echo "============================================"

echo ""
echo "[1/6] A verificar o Minikube..."
if ! minikube status > /dev/null 2>&1; then
    echo "Minikube nao esta a correr. A iniciar..."
    minikube start --driver=docker
else
    echo "Minikube ja esta a correr."
fi

echo ""
echo "[2/6] A configurar o Docker do Minikube..."
eval $(minikube docker-env)

echo ""
echo "[3/6] A construir as imagens Docker..."
docker build -t servico-utilizadores:latest ./servico-utilizadores
docker build -t servico-autenticacao:latest ./servico-autenticacao
docker build -t servico-tarefas:latest ./servico-tarefas
docker build -t servico-notificacoes:latest ./servico-notificacoes
docker build -t orquestrador:latest ./orquestrador
docker build -t frontend:latest ./frontend

echo "Imagens construidas com sucesso."

echo ""
echo "[4/6] A aplicar os manifests do Kubernetes..."
kubectl apply -f kubernetes/segredos.yaml
kubectl apply -f kubernetes/mariadb.yaml

echo "A aguardar que o MariaDB fique pronto..."
kubectl wait --for=condition=ready pod -l app=mariadb --timeout=120s

kubectl apply -f kubernetes/servico-utilizadores.yaml
kubectl apply -f kubernetes/servico-autenticacao.yaml
kubectl apply -f kubernetes/servico-tarefas.yaml
kubectl apply -f kubernetes/servico-notificacoes.yaml
kubectl apply -f kubernetes/orquestrador.yaml
kubectl apply -f kubernetes/frontend.yaml

echo ""
echo "[5/6] A verificar o estado dos pods..."
sleep 10
kubectl get pods
kubectl get services

echo ""
echo "[6/6] A iniciar port-forward..."

pkill -f "kubectl port-forward" 2>/dev/null || true
sleep 1

kubectl port-forward --address 0.0.0.0 service/orquestrador 5000:5000 &
kubectl port-forward --address 0.0.0.0 service/frontend 8080:80 &

sleep 3

echo ""
echo "============================================"
echo "  Deploy concluido!"
echo ""
echo "  Frontend: http://localhost:8080"
echo "  API:      http://localhost:5000"
echo ""
echo "  Para parar: minikube stop"
echo "============================================"
