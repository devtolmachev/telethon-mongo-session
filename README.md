<h1 align="center">Telethon MultiMongoDB Session</h1>

<h3 align="center">Summary</h3>
<p align="center">
    <img src=".github/badges/coverage.svg" alt="Test Coverage">
    <img src="https://img.shields.io/badge/Python_versions-^3.11-green" alt="Python Versions">
    <img src="https://img.shields.io/badge/License-Apache_2.0-green" alt="License">
    <img src="https://img.shields.io/badge/style-ruff-rgb(208, 90, 16)" alt="Style">
    <img src="https://img.shields.io/badge/linter-ruff-black" alt="Linter">
</p>

<h3 align="center">Codebase</h3>
<p align="center">
    <img src="https://img.shields.io/badge/Code_Lines-482-yellow" alt="Codelines">
    <img src="https://img.shields.io/badge/Code_Symbols-13614-yellow" alt="Codesymbols">

</p>

<h3 align="center">Other</h3>
<p align="center">
    <img src="https://img.shields.io/badge/Develop_on-Arch_Linux-blue" alt="Develop on Arch Linux">
    <img src="https://img.shields.io/badge/Developers-1-red" alt="Developers count">
</p>


# Table of Contents

- [Table of Contents](#table-of-contents)
- [Overwriew](#overwriew)
- [Installation](#installation)
- [Examples](#examples)
- [Testing](#testing)


# Overwriew

This is a python library for store your telethon sessions in mongodb database. 
The main feature is that you can store several telethon sessions in one 
Mongodb database.

> [!TIP]
> This is achieved due to the fact that each session is a single 
> document that has a unique composite key (phone number, API ID, API Hash)

# Installation

```bash
pip install telethon-multimongo-session
```

# Examples

```python
import pymongo
import telethon as th
from telethon_multimongo_session import MongoSession

session = MongoSession(
    api_id=API_ID,
    api_hash=API_HASH,
    phone=PHONE_NUMBER,
    database=MONGODB_TEST_DBNAME,
    coll=MONGODB_TEST_COLL,
    host=MONGODB_HOST,
    port=MONGODB_PORT,
)
client = th.TelegramClient(session, api_id=API_ID, api_hash=API_HASH)
# Set dc for test servers
dc_id = int(PHONE_NUMBER[5])
# Get dc ip
ip = TELEGRAM_DATA_CENTERS_IP[dc_id] 
# Set dc in session
client.session.set_dc(dc_id, ip, 80)

# Connect to telegram and write some data to session
await telethon.start(phone=PHONE_NUMBER, code_callback=lambda: CODE)
me = await telethon.get_me()
assert me

```

# Testing

Tests stored in `tests/` directory, you may also run all tests by typing in terminal `make tests`
