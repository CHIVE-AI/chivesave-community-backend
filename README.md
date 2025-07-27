# ChiveSave AI Versioning Backend

  

![ChiveSave Logo](https://olive-chemical-haddock-701.mypinata.cloud/ipfs/bafybeiflqcxurn3r6dbptaq242ao2ybe3fzh2g2ng7pz2nxys3vvqm3dwy)

 <div align="center">
  <a href="https://x.com/version_chive">[Twitter / X]</a> | <a href="https://letsbonk.fun/token/SOON">[Buy $Chive]</a> | <a href="https://github.com/CHIVE-AI">[Contributing]</a>
</div>

 ```
 ```

Welcome to **ChiveSave**, a self-hosted, open-source AI artifact versioning backend built for the community! This project provides a robust and scalable solution for managing your AI models, datasets, and configurations, ensuring you can track, preview, restore, and refactor your valuable AI assets with ease.

  

Built with Python's FastAPI and PostgreSQL, ChiveSave is designed for performance, reliability, and ease of use, making it perfect for individual researchers, small teams, or community-driven AI initiatives.

  

## ✨ Features

  

ChiveSave offers core functionalities to streamline your AI development workflow:

  

* **ChiveSave (Version Saving)**:

* Securely upload and store new versions of your AI artifacts (models, datasets, config files).

* Attach descriptive names, detailed descriptions, and custom JSON metadata to each version for rich context.

* **Preview (Version Inspection)**:

* Retrieve comprehensive metadata and details for any specific AI artifact version.

* Understand what's in a version without needing to download the actual file.

* **Restore (Version Activation)**:

* Activate any previous version of an artifact by copying it to a designated "current active" directory.

* Seamlessly switch between different model or dataset versions for testing or deployment.

* **RefactorEditor / Refactor Guidance**:

* While refactoring is typically done with external tools, ChiveSave provides clear guidance on how to integrate your refactored artifacts back into the versioning system as new, traceable versions.

* Maintain a clear lineage of your refactored assets.

* **Versiondatabase (PostgreSQL Backend)**:

* Leverages PostgreSQL for reliable and efficient storage of all version metadata.

* Ensures data integrity and scalability for your versioning needs.

* **Authentication & Authorization**:

* Secure API endpoints using JWT (JSON Web Tokens).

* User registration and login functionality.

* Role-based access control (e.g., admin users for user management).

* **Structured Configuration**: Utilizes `pydantic-settings` for type-safe and organized management of environment variables.

* **API Versioning**: All API endpoints are prefixed with `/v1/` for clear version management and future extensibility.

* **Asynchronous Operations**: Built with FastAPI and `asyncpg` for non-blocking I/O, ensuring high performance and responsiveness.

* **Structured Logging**: Comprehensive logging throughout the application for easy monitoring and debugging.

* **Containerization**: Includes `Dockerfile` and `docker-compose.yml` for easy setup, consistent development environments, and simplified deployment.

  

## 🚀 Technologies Used

  

* **Backend Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python)

* **Asynchronous Database Driver**: [asyncpg](https://magicstack.github.io/asyncpg/)

* **Database**: [PostgreSQL](https://www.postgresql.org/)

* **Asynchronous File I/O**: [aiofiles](https://github.com/Tinche/aiofiles)

* **Data Validation**: [Pydantic](https://pydantic-docs.helpmanual.io/)

* **Authentication**: [python-jose](https://python-jose.readthedocs.io/en/latest/) (JWT) and [passlib](https://passlib.readthedocs.io/en/stable/) (password hashing)

* **Configuration**: [pydantic-settings](https://pydantic-settings.readthedocs.io/en/latest/)

  

## 🛠️ Setup and Installation

  

The easiest way to get ChiveSave running is using Docker Compose, which will manage both the PostgreSQL database and the FastAPI application.

  

### Prerequisites

  

* [Docker](https://docs.docker.com/get-docker/) (Docker Engine and Docker Compose)

* Python 3.8+ (if running without Docker, for development)

  

### 1. Clone the Repository

  

(Assuming you have the code in your current directory, if not, you'd clone it here)

  

### 2. Configure Environment Variables

  

Create a `.env` file in the root directory of the project (next to `Dockerfile` and `docker-compose.yml`). This file will store sensitive information like your JWT secret key.

  

    dotenv

# .env

    SECRET_KEY="your-very-long-and-random-secret-key-for-jwt-signing"

#### You can override DATABASE_URL here if not using docker-compose default

#### DATABASE_URL="postgresql://user:password@localhost:5432/chivesave_db"


**IMPORTANT**: Replace `"your-very-long-and-random-secret-key-for-jwt-signing"` with a strong, randomly generated secret key. **Do not use this default in production!**

  

### 3. Build and Run with Docker Compose

  

Navigate to the project root directory in your terminal and run:

  

    #bash
    docker compose up --build -d


  

This command will:

* Build the `chivesave_app` Docker image based on the `Dockerfile`.

* Start the `chivesave_db` PostgreSQL container.

* Start the `chivesave_app` container, which will automatically connect to the database and initialize the schema (creating `versions` and `users` tables).

* The `-d` flag runs the services in detached mode (in the background).

  

### 4. Verify Services

You can check the status of your running containers:

    #bash
    docker compose ps

  

You should see `chivesave_db` and `chivesave_app` in a healthy state.

  

## 📚 API Documentation

  

Once the server is running, you can access the interactive API documentation (Swagger UI) at:

  

👉 [http://localhost:8000/docs](http://localhost:8000/docs)

  

This documentation allows you to explore all available endpoints, their parameters, and expected responses, and even test them directly from your browser.

  

## 🔒 Testing Authentication

  

All core versioning endpoints are protected and require authentication.

  

1. **Create an Admin User**:

* Go to `http://localhost:8000/docs`.

* Find the `POST /v1/users/` endpoint under "Authentication".

* Click "Try it out".

* In the `Request body`, provide a `username`, `password`, and set `roles` to `["admin"]`.

* Execute the request. You should get a `201 Created` response.

* **Note**: For initial setup, this endpoint is accessible. In a production environment, you would typically seed the first admin user securely or protect this endpoint after initial deployment.

2. **Get an Access Token**:

* Find the `POST /v1/token` endpoint under "Authentication".

* Click "Try it out".

* Enter the `username` and `password` of the admin user you just created.

* Execute the request. You will receive an `access_token` (a long string).

3. **Authorize in Swagger UI**:

* Click the "Authorize" button at the top right of the Swagger UI.

* In the dialog, select "OAuth2PasswordBearer (apiKey)".

* Paste your `access_token` (just the token string, **without** "Bearer ") into the "Value" field.

* Click "Authorize" and then "Close".

4. **Test Protected Endpoints**:

* Now, try any of the `/v1/versions/*` or `/v1/users/` (GET) endpoints. They should work, as you are now authenticated.

* Attempting to access these without authorization, or with an invalid token, will result in a `401 Unauthorized` error.

  

## 📁 Project Structure

```
.
├── .env
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── README.md
├── LICENSE
├── artifacts/
├── current_active_artifact/
└── app/
    ├── main.py
    ├── core/
    ├── db/
    ├── models/
    ├── crud/
    ├── services/
    └── api/
        └── v1/
            └── endpoints/
```

## 🤝 Contributing

  

We welcome contributions from the community! Whether it's bug reports, feature requests, code improvements, or documentation enhancements, your help is valuable.

  

1. Fork the repository.

2. Create a new branch (`git checkout -b feature/your-feature-name`).

3. Make your changes and ensure tests pass (if any).

4. Commit your changes (`git commit -m 'feat: Add new feature X'`).

5. Push to the branch (`git push origin feature/your-feature-name`).

6. Open a Pull Request.

  

Please ensure your code adheres to good practices, includes type hints, and has clear docstrings.

  

## 📄 License

  

This project is licensed under the [MIT License](LICENSE).

  

## 📧 Contact

  

If you have any questions, suggestions, or need support, feel free to open an issue on the GitHub repository.

  

---

  

Happy AI Versioning with ChiveSave!