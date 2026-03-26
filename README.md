# WhatsApp QR Automation Relay

A lightweight automation system that listens for QR-code links posted in a WhatsApp group and opens them automatically inside isolated browser sessions.

This project was built to automate repetitive browser-opening tasks from WhatsApp messages, using a **master/worker architecture** with **Redis streams**, **Selenium**, and **systemd-managed Linux services** on an Azure VM.

---

## Overview

The system continuously monitors a specific WhatsApp group through **WhatsApp Web**.

When a message containing a target QR URL is detected:

1. the **master process** extracts the URL,
2. publishes it to a **Redis stream**,
3. and one or more **worker processes** consume the event and open the page in their own browser session.

This design allows the system to scale horizontally by adding multiple browser workers, each with an isolated Chrome profile.

---

## Main Features

- **WhatsApp Web monitoring**
- **Automatic detection of QR-related URLs**
- **Redis-based event streaming**
- **Worker-based browser automation**
- **Independent Chrome profiles per worker**
- **Headless/background deployment on Linux**
- **Persistent execution with systemd services**
- **Scalable architecture for multiple browser consumers**

---

## Architecture

```text
WhatsApp Group Message
        │
        ▼
whatsapp_bot_vm.py   (MASTER)
        │
        │ extracts QR URL
        ▼
Redis Stream (stream:whatsapp)
        │
        ├── worker_stream.py (worker-01)
        ├── worker_stream.py (worker-02)
        ├── worker_stream.py (worker-03)
        └── ...
                │
                ▼
      Selenium opens the QR URL
      in isolated browser sessions
