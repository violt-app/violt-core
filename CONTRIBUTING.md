# Contributing to Violt Core

We're excited that you're interested in contributing to Violt Core! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](./CODE_OF_CONDUCT.md).

## How to Contribute

### Reporting Bugs

If you find a bug in the project, please create an issue on GitHub with the following information:

- A clear, descriptive title
- Steps to reproduce the issue
- Expected behavior
- Actual behavior
- Screenshots or logs (if applicable)
- Environment information (OS, browser, etc.)

### Suggesting Features

We welcome feature suggestions! Please create an issue on GitHub with the following information:

- A clear, descriptive title
- A detailed description of the proposed feature
- Any relevant mockups or diagrams
- Use cases for the feature

### Pull Requests

1. Fork the repository
2. Create a new branch: `git checkout -b feature/my-feature` or `bugfix/issue-description`
3. Make your changes
4. Run tests to ensure your changes don't break existing functionality
5. Commit your changes using conventional commit messages
6. Push to your fork: `git push origin feature/my-feature`
7. Create a pull request to the `main` branch

## Development Setup

### Backend

1. Set up a virtual environment:

   ```
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Install development dependencies:

   ```
   pip install -r requirements-dev.txt
   ```

3. Set up pre-commit hooks:

   ```
   pre-commit install
   ```

4. Run the development server:

   ```
   uvicorn app.main:app --reload
   ```

### Frontend

1. Install dependencies:

   ```
   cd frontend
   npm install
   ```

2. Run the development server:

   ```
   npm run dev
   ```

## Testing

### Backend Tests

Run the backend tests with pytest:

```
cd backend
pytest
```

For coverage report:

```
pytest --cov=app
```

### Frontend Tests

Run the frontend tests with Jest:

```
cd frontend
npm test
```

## Code Style

### Backend

We follow PEP 8 style guide for Python code. We use:

- Black for code formatting
- isort for import sorting
- flake8 for linting

You can run these tools with:

```
cd backend
black .
isort .
flake8
```

### Frontend

We follow the Airbnb JavaScript Style Guide. We use:

- ESLint for linting
- Prettier for code formatting

You can run these tools with:

```
cd frontend
npm run lint
npm run format
```

## Commit Messages

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification for commit messages:

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

Types include:

- feat: A new feature
- fix: A bug fix
- docs: Documentation changes
- style: Changes that do not affect the meaning of the code
- refactor: Code changes that neither fix a bug nor add a feature
- perf: Performance improvements
- test: Adding or correcting tests
- chore: Changes to the build process or auxiliary tools

## Branch Organization

- `main`: The main branch contains the stable version of the code
- `develop`: The development branch contains the latest changes
- Feature branches: Named as `feature/feature-name`
- Bugfix branches: Named as `bugfix/issue-description`

## Release Process

1. Merge feature branches into `develop`
2. Create a release branch: `release/vX.Y.Z`
3. Perform final testing and version bumping
4. Merge the release branch into `main` and tag the release
5. Merge `main` back into `develop`

## License

By contributing to Violt Core, you agree that your contributions will be licensed under the project's [GNU AFFERO GENERAL PUBLIC LICENSE](./LICENSE).
