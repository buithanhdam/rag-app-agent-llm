pipeline {
    agent any

    options {
        buildDiscarder(logRotator(numToKeepStr: '5', daysToKeepStr: '5'))
        timestamps()
        disableConcurrentBuilds()
    }

    environment {
        DOCKER_REGISTRY = "docker.io"
        DOCKER_NAMESPACE = "buithanhmdam02"
        DOCKER_REPO_BACKEND = "rag-agent-llm-backend"
        DOCKER_REPO_FRONTEND = "rag-agent-llm-frontend"
        DOCKER_IMAGE_BACKEND = "${DOCKER_REGISTRY}/${DOCKER_NAMESPACE}/${DOCKER_REPO_BACKEND}:${BUILD_NUMBER}"
        DOCKER_IMAGE_FRONTEND = "${DOCKER_REGISTRY}/${DOCKER_NAMESPACE}/${DOCKER_REPO_FRONTEND}:${BUILD_NUMBER}"
        DOCKER_REGISTRY_CREDENTIAL = 'dockerhub'
        BACKEND_ENV = credentials('backend-env')
        FRONTEND_ENV = credentials('frontend-env')
        DOCKER_FRONTEND = credentials('docker-frontend-creds')
        DOCKER_BACKEND = credentials('docker-backend-creds')
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Docker Images') {
            steps {
                script {
                    echo 'Building Docker images...'
                    dir('backend') {
                        dockerImageBackend = docker.build("${DOCKER_IMAGE_BACKEND}", "--platform=linux/amd64 -f ./backend/docker/Dockerfile.backend .")
                    }
                    dir('frontend') {
                        dockerImageFrontend = docker.build("${DOCKER_IMAGE_FRONTEND}", "--platform=linux/amd64 -f ./frontend/docker/Dockerfile.frontend .")
                    }
                }
            }
        }

        stage('Push Docker Images') {
            steps {
                script {
                    echo 'Pushing Docker images to registries...'
                    docker.withRegistry('', DOCKER_REGISTRY_CREDENTIAL) {
                        dockerImageBackend.push()
                        dockerImageBackend.push('latest')

                        dockerImageFrontend.push()
                        dockerImageFrontend.push('latest')
                    }
                }
            }
        }

        stage('Prepare Deployment') {
            steps {
                script {
                    echo "Preparing for deployment..."
                    sh "cp $BACKEND_ENV backend/.env"
                    sh "cp $FRONTEND_ENV frontend/.env"
                    sh "docker compose version || (echo 'docker compose not found' && exit 1)"
                }
            }
        }

        stage('Deploy') {
            steps {
                script {
                    echo "Deploying the application..."
                    sh "docker compose -f docker-compose.yaml up -d"
                    sh """
                    sleep 10
                    if ! docker compose -f docker-compose.yaml ps | grep Up; then
                        echo "Deployment failed - containers are not running"
                        exit 1
                    fi
                    """
                }
            }
        }

        stage('Health Check') {
            steps {
                script {
                    // Check backend health
                    sh 'curl --retry 10 --retry-delay 5 http://localhost:8000/health'
                    
                    // Check frontend health
                    sh 'curl --retry 10 --retry-delay 5 http://localhost:3000'
                }
            }
        }

        stage('Cleanup') {
            steps {
                script {
                    echo "Cleaning up resources..."
                    sh "docker compose -f docker-compose.yaml down --remove-orphans"
                    sh "docker system prune -af --volumes"
                    sh "docker rmi ${DOCKER_IMAGE_BACKEND} ${DOCKER_IMAGE_FRONTEND} || true"
                    sh "docker rmi ${DOCKER_REGISTRY}/${DOCKER_NAMESPACE}/${DOCKER_REPO_BACKEND}:latest ${DOCKER_REGISTRY}/${DOCKER_NAMESPACE}/${DOCKER_REPO_FRONTEND}:latest || true"
                }
            }
        }
    }

    post {
        always {
            script {
                sh 'rm -f backend/.env frontend/.env'
                sh 'docker image prune -f'
            }
        }
        success {
            echo 'Build and Deployment successful.'
        }
        failure {
            echo 'Build or Deployment failed!'
            sh 'docker-compose -f backend/docker-compose-backend.yml down'
            sh 'docker-compose -f frontend/docker-compose-frontend.yml down'
        }
    }
}