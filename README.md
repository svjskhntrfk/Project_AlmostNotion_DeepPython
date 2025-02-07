# MindSpace - Task Management Platform

## Overview
MindSpace is a collaborative task management platform that helps users organize their work through boards, tasks, and to-do lists. Built with FastAPI and modern web technologies, it offers a user-friendly interface for managing projects and tasks.

## Features
- 👤 User Authentication
  - Email-based registration and login
  - JWT token-based authentication
  - Password validation and security

- 📋 Boards Management
  - Create multiple boards per user
  - Collaborative board sharing
  - Text content creation and editing

- ✅ Task Management
  - Create to-do lists with deadlines
  - Task completion tracking
  - Email notifications for upcoming deadlines

- 🖼️ Media Support
  - Profile picture upload
  - S3-compatible storage integration
  - Image optimization and WebP conversion

## Tech Stack
### Backend
- FastAPI
- SQLAlchemy (Async)
- PostgreSQL
- JWT Authentication
- APScheduler for notifications

### Frontend
- HTML/CSS
- JavaScript
- Jinja2 Templates

### Storage
- S3-compatible object storage
- PostgreSQL database

### Infrastructure
- Docker containerization
- SMTP email integration (Gmail)
