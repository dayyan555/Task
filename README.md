# Multi-User Real-Time Chat Application

This is a FastAPI-based real-time chat application that allows multiple users to create, join, and communicate in chat rooms. The application supports WebSocket for real-time messaging and provides a RESTful API for managing users and chat rooms.

## Features

- User Registration & Authentication
- Create, Join, and Leave Chat Rooms
- Real-Time Messaging via WebSockets
- Retrieve Chat Room Messages and Users
- RESTful API for Chat Management

## Getting Started

### 1. Clone the Repository

```sh
git clone https://github.com/dayyan555/Task.git
cd Task
```

### 2. Build and Start the Application

#### Build Docker Containers (without cache)

```sh
docker-compose build --no-cache
```

#### Start the Application in Detached Mode

```sh
docker-compose up -d
```

The API will be available at: [**http://localhost:8000/**](http://localhost:8000/)

## API Endpoints

### Authentication

#### **Register a User**

**POST** `/api/register`

```json
{
  "username": "string",
  "email": "string",
  "password": "string"
}
```

#### **User Login**

**POST** `/api/login`

```json
{
  "username": "string",
  "password": "string"
}
```

#### **User Logout**

**POST** `/api/logout`

#### **Delete User Account**

**DELETE** `/api/delete`

### Chat Room Management

#### **Create a Chat Room**

**POST** `/api/chat/rooms`

```json
{
  "name": "new chat"
}
```

#### **Get All Chat Rooms**

**GET** `/api/chat/rooms`

#### **Get Chat Room Details**

**GET** `/api/chat/rooms/{room_id}`

#### **Join a Chat Room**

**POST** `/api/chat/rooms/{room_id}/join`

#### **Leave a Chat Room**

**POST** `/api/chat/rooms/{room_id}/leave`

#### **Get Chat Room Users**

**GET** `/api/chat/rooms/{room_id}/users`

#### **Get Chat Room Messages**

**GET** `/api/chat/rooms/{room_id}/messages`

## WebSocket for Real-Time Messaging

Connect to the WebSocket server to send and receive messages in real-time.

**WebSocket URL:**

```
ws://localhost:8000/ws/chat/{room_id}?token={token}
```

**Sample WebSocket Message Payload:**

```json
{
    "text": "hammad here, how are you all"
}
```

## Testing the API

### Swagger UI

After starting the application, open your browser and go to:

```
http://localhost:8000/docs
```

This will display an interactive API documentation where you can test all endpoints.

### Using Postman

You can also test the API endpoints manually by using [Postman](https://www.postman.com/) or any other API testing tool.

## Stopping the Application

To stop and remove the running containers:

```sh
docker-compose down
```

## License

This project is licensed under the MIT License.

---

**Happy Chatting! 🎉**

