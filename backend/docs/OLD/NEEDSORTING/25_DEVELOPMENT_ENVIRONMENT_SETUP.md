# DEVELOPMENT ENVIRONMENT SETUP

## Overview

This document provides a comprehensive guide to setting up the development environment for the NOVAMIND platform. It covers all the necessary steps to ensure a consistent and efficient development experience across the team.

## 1. Prerequisites

Before setting up the development environment, ensure you have the following prerequisites installed:

- **Python 3.11+**: The NOVAMIND platform requires Python 3.11 or higher.
- **PostgreSQL 14+**: The primary database for the platform.
- **Docker & Docker Compose**: For containerized development and testing.
- **Git**: For version control.
- **WSL2** (for Windows users): For a Linux-compatible development environment.
- **Visual Studio Code**: Recommended IDE for development.

## 2. Repository Setup

Clone the repository and set up the development environment:

```bash
# Clone the repository
git clone https://github.com/your-organization/novamind-backend.git
cd novamind-backend

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows
venv\Scripts\activate
# On Linux/macOS
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install the package in development mode
pip install -e .
```

## 3. WSL2-Windows Integration

For Windows users, set up WSL2 integration for seamless file visibility and editing:

```bash
# From WSL2, create symlinks for all project directories
ln -s /mnt/c/Users/JJ/Desktop/NOVAMIND-WEB/Novamind-Backend /home/username/novamind-backend

# For specific directories that need Windows visibility
mkdir -p /mnt/c/Users/JJ/Desktop/NOVAMIND-WEB/Novamind-Backend/app/core/utils
cp -r /home/username/novamind-backend/app/core/utils/* /mnt/c/Users/JJ/Desktop/NOVAMIND-WEB/Novamind-Backend/app/core/utils/

# Set appropriate permissions
chmod -R 755 /mnt/c/Users/JJ/Desktop/NOVAMIND-WEB/Novamind-Backend
```

## 4. Environment Configuration

Create a `.env` file in the root directory with the following configuration:

```bash
# Database
DB_HOST=localhost
DB_PORT=5432
DB_USERNAME=postgres
DB_PASSWORD=postgres
DB_NAME=novamind
DB_ECHO=True

# JWT
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Logging
LOG_LEVEL=DEBUG
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s
LOG_FILE=logs/novamind.log

# AWS
AWS_ACCESS_KEY=your-access-key
AWS_SECRET_KEY=your-secret-key
AWS_REGION=us-east-1
AWS_S3_BUCKET=novamind-bucket

# OpenAI
OPENAI_API_KEY=your-api-key
OPENAI_MODEL=gpt-4

# SMTP
SMTP_HOST=localhost
SMTP_PORT=25
SMTP_USERNAME=your-username
SMTP_PASSWORD=your-password
FROM_EMAIL=no-reply@novamind.com

# Twilio
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_PHONE_NUMBER=+15555555555
```

## 5. Database Setup

Set up the PostgreSQL database:

```bash
# Create the database
createdb novamind

# Run migrations
alembic upgrade head
```

## 6. Docker Setup

Set up Docker for containerized development and testing:

```bash
# Build the Docker image
docker-compose build

# Start the services
docker-compose up -d

# Stop the services
docker-compose down
```

## 7. IDE Configuration

### Visual Studio Code

Configure Visual Studio Code for optimal development experience:

1. Install the following extensions:
   - Python
   - Pylance
   - Docker
   - Remote - WSL (for Windows users)
   - GitLens
   - Python Test Explorer
   - Python Docstring Generator
   - autoDocstring
   - Black Formatter
   - Flake8
   - isort

2. Configure settings.json:

```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.mypyEnabled": true,
    "python.formatting.provider": "black",
    "python.formatting.blackArgs": [
        "--line-length",
        "88"
    ],
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    },
    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": false,
    "python.testing.nosetestsEnabled": false,
    "python.testing.pytestArgs": [
        "tests"
    ],
    "python.linting.flake8Args": [
        "--max-line-length=88",
        "--extend-ignore=E203"
    ],
    "python.linting.mypyArgs": [
        "--ignore-missing-imports",
        "--disallow-untyped-defs",
        "--disallow-incomplete-defs"
    ],
    "[python]": {
        "editor.rulers": [
            88
        ]
    }
}
```

3. Configure launch.json for debugging:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: FastAPI",
            "type": "python",
            "request": "launch",
            "module": "uvicorn",
            "args": [
                "app.main:app",
                "--reload",
                "--host",
                "0.0.0.0",
                "--port",
                "8000"
            ],
            "jinja": true,
            "justMyCode": false
        },
        {
            "name": "Python: Current File",
            "type": "python",
            "request": "launch",
            "program": "${file}",
            "console": "integratedTerminal",
            "justMyCode": false
        },
        {
            "name": "Python: Debug Tests",
            "type": "python",
            "request": "launch",
            "program": "${file}",
            "purpose": [
                "debug-test"
            ],
            "console": "integratedTerminal",
            "justMyCode": false
        }
    ]
}
```

## 8. Pre-commit Hooks

Set up pre-commit hooks to ensure code quality:

```bash
# Install pre-commit
pip install pre-commit

# Install pre-commit hooks
pre-commit install
```

Create a `.pre-commit-config.yaml` file in the root directory:

```yaml
repos:
-   repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
    -   id: trailing-whitespace
    -   id: end-of-file-fixer
    -   id: check-yaml
    -   id: check-added-large-files
    -   id: check-ast
    -   id: check-json
    -   id: check-merge-conflict
    -   id: detect-private-key

-   repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
    -   id: isort
        args: ["--profile", "black"]

-   repo: https://github.com/psf/black
    rev: 23.9.1
    hooks:
    -   id: black
        args: ["--line-length", "88"]

-   repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
    -   id: flake8
        args: ["--max-line-length=88", "--extend-ignore=E203"]

-   repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.6.1
    hooks:
    -   id: mypy
        args: ["--ignore-missing-imports", "--disallow-untyped-defs", "--disallow-incomplete-defs"]
        additional_dependencies: [types-requests, types-PyYAML, sqlalchemy-stubs]

-   repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
    -   id: bandit
        args: ["-c", "pyproject.toml"]
        additional_dependencies: ["bandit[toml]"]
```

## 9. Running the Application

Run the application in development mode:

```bash
# Run the application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 10. Development Workflow

Follow these steps for a smooth development workflow:

1. **Create a Feature Branch**: Create a new branch for each feature or bug fix.

```bash
git checkout -b feature/your-feature-name
```

2. **Write Tests**: Write tests for your feature or bug fix.

```bash
# Run tests
pytest tests/
```

3. **Implement the Feature**: Implement the feature or bug fix.

4. **Run Linters and Formatters**: Run linters and formatters to ensure code quality.

```bash
# Run black
black app/ tests/

# Run isort
isort app/ tests/

# Run flake8
flake8 app/ tests/

# Run mypy
mypy app/ tests/
```

5. **Run Tests**: Run tests to ensure your feature or bug fix works as expected.

```bash
# Run tests
pytest tests/
```

6. **Commit Changes**: Commit your changes with a descriptive commit message.

```bash
git add .
git commit -m "Add your feature or fix your bug"
```

7. **Push Changes**: Push your changes to the remote repository.

```bash
git push origin feature/your-feature-name
```

8. **Create a Pull Request**: Create a pull request to merge your changes into the main branch.

## 11. Troubleshooting

### Common Issues

1. **Database Connection Issues**:
   - Ensure PostgreSQL is running.
   - Check the database credentials in the `.env` file.
   - Verify that the database exists.

2. **Dependency Issues**:
   - Ensure you have activated the virtual environment.
   - Try reinstalling the dependencies: `pip install -r requirements.txt`.

3. **WSL2 Integration Issues**:
   - Ensure WSL2 is installed and configured correctly.
   - Check the file permissions.
   - Verify that the symlinks are set up correctly.

4. **Docker Issues**:
   - Ensure Docker is running.
   - Check the Docker logs: `docker-compose logs`.
   - Try rebuilding the Docker image: `docker-compose build`.

## Conclusion

This development environment setup guide provides a comprehensive approach to setting up the development environment for the NOVAMIND platform. By following these guidelines, you can ensure a consistent and efficient development experience across the team.