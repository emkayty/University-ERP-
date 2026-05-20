# University MIS Ansible Configuration

## Requirements
- Ansible 2.12+
- kubectl access to target cluster
- Python 3.8+

## Usage

### Deploy to K3s
```bash
ansible-playbook -i inventory/prod.yml playbooks/deploy.yml
```

### Deploy to K8s (Production)
```bash
ansible-playbook -i inventory/prod.yml playbooks/deploy-k8s.yml
```

### Setup Development Environment
```bash
ansible-playbook -i inventory/dev.yml playbooks/setup-dev.yml
```

### Database Backup
```bash
ansible-playbook -i inventory/prod.yml playbooks/backup.yml
```

## Inventory Structure
```
inventory/
  dev.yml      # Development environment
  staging.yml  # Staging environment  
  prod.yml     # Production environment
```

## Playbooks
```
playbooks/
  deploy.yml       # Deploy to K3s
  deploy-k8s.yml  # Deploy to Kubernetes
  setup-dev.yml   # Setup development environment
  backup.yml      # Database backup
  restore.yml     # Database restore
```