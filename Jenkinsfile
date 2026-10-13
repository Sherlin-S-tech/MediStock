pipeline {
  agent { label 'linux' }

  options {
    skipDefaultCheckout(true)
    timestamps()
    disableConcurrentBuilds()
  }

  triggers {
    githubPush()
  }

  parameters {
    string(name: 'APP_IMAGE', defaultValue: 'medicine-stock', description: 'Lowercase Docker image name, optionally with namespace (for example owner/medicine-stock)')
    string(name: 'APP_TAG_OVERRIDE', defaultValue: '', description: 'Optional Docker tag override; leave blank to use the checked-out commit SHA')
    booleanParam(name: 'DEPLOY_ENABLED', defaultValue: false, description: 'Deploy the tested image to the configured Ansible target')
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
        script {
          def imageName = params.APP_IMAGE?.trim()
          if (!imageName || !(imageName ==~ /^[a-z0-9]+(?:[._-][a-z0-9]+)*(?:\/[a-z0-9]+(?:[._-][a-z0-9]+)*)*$/)) {
            error('APP_IMAGE must be a lowercase Docker image name, optionally with namespace.')
          }

          def tag = params.APP_TAG_OVERRIDE?.trim()
          if (!tag) {
            tag = env.GIT_COMMIT ? env.GIT_COMMIT.take(12) : env.BUILD_NUMBER
          }
          if (!(tag ==~ /^[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}$/)) {
            error('APP_TAG_OVERRIDE is not a valid Docker tag.')
          }

          env.APP_IMAGE_NAME = imageName
          env.APP_TAG = tag
          env.TESTED_IMAGE = "${imageName}:${tag}"
          echo "Building ${env.TESTED_IMAGE} from ${env.GIT_COMMIT ?: 'the selected revision'}"
        }
      }
    }

    stage('Setup Dependencies') {
      steps {
        sh 'python3 -m venv .venv && .venv/bin/python -m pip install -r requirements.txt'
      }
    }

    stage('Syntax Validation') {
      steps {
        sh '''
          .venv/bin/python -m py_compile app.py database.py demo_data.py services.py scripts/seed_demo_data.py
          .venv/bin/python -c "import yaml; [yaml.safe_load(open(p, encoding='utf-8')) for p in ['ansible/deploy.yml','ansible/manage_container.yml']]"
          ansible-playbook --syntax-check -i ansible/inventory.ini ansible/deploy.yml
          ansible-playbook --syntax-check -i ansible/inventory.ini ansible/manage_container.yml
          docker compose config --quiet
        '''
      }
    }

    stage('Automated Tests') {
      steps {
        sh 'PYTHONPATH="$WORKSPACE" .venv/bin/pytest -q --junitxml=test-results.xml'
      }
      post {
        unsuccessful {
          junit allowEmptyResults: true, testResults: 'test-results.xml'
        }
      }
    }

    stage('Publish Test Results') {
      steps {
        script {
          if (fileExists('test-results.xml')) {
            junit allowEmptyResults: true, testResults: 'test-results.xml'
          } else {
            echo 'No JUnit report was generated.'
          }
        }
      }
    }

    stage('Build Docker Image') {
      steps {
        sh 'docker build --tag "$TESTED_IMAGE" .'
      }
    }

    stage('Deploy with Ansible') {
      when {
        expression { return params.DEPLOY_ENABLED }
      }
      steps {
        withCredentials([string(credentialsId: 'medicine-stock-secret-key', variable: 'MEDICINE_STOCK_SECRET_KEY')]) {
          sh 'ansible-playbook -i ansible/inventory.ini ansible/deploy.yml --extra-vars "app_image=$TESTED_IMAGE"'
        }
      }
    }

    stage('Verify Deployment') {
      when {
        expression { return params.DEPLOY_ENABLED }
      }
      steps {
        sh 'ansible -i ansible/inventory.ini medicine_hosts -m ansible.builtin.uri -a "url=http://127.0.0.1:5000/health status_code=200"'
      }
    }
  }

  post {
    success {
      echo "Pipeline succeeded for ${env.TESTED_IMAGE ?: 'the selected revision'}"
    }
    failure {
      echo 'Pipeline failed. Review the first failed stage and its console output. Docker build and deployment require successful tests.'
    }
    aborted {
      echo 'Pipeline was aborted before completion.'
    }
  }
}
