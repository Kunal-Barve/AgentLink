# Hostinger VPS SSH Key Setup Guide

## Server Information

- **VPS Provider**: Hostinger
- **Server Purpose**: n8n Automation Platform
- **Server IP**: 72.62.64.72
- **Username**: root

## SSH Key Details

- **Private Key Name**: `agentlink-hostinger-n8n`
- **Public Key Name**: `agentlink-hostinger-n8n.pub`
- **Key Type**: ED25519 (256-bit)
- **Key Location**: `D:\Articflow\ssh-keys\`

## What is a Passphrase?

### Understanding SSH Key Passphrase

A **passphrase** is an additional layer of security for your SSH private key. Think of it as a password that protects your private key file.

### How It Works

1. **Private Key**: Your SSH private key is like a physical key to your house
2. **Passphrase**: The passphrase is like a safe that holds your physical key

Even if someone steals your private key file, they cannot use it without knowing the passphrase.

### Passphrase vs Password

- **Password**: Used to log into a server directly
- **Passphrase**: Used to unlock/decrypt your private key before it can be used

### When to Use a Passphrase

**Use a passphrase if:**
- You're storing keys on a shared computer
- You're worried about physical theft of your device
- You want maximum security
- You access the server infrequently

**Skip passphrase if:**
- You need automated access (CI/CD, scripts)
- Your computer is physically secure
- You're the only user
- You use encrypted drive/folder for keys

### In Our Case

For the `agentlink-hostinger-n8n` key, we chose **no passphrase** (pressed Enter twice) because:
- Keys are stored locally on a secure machine
- We may need automated deployment access
- The key location folder is already protected

## Setup Steps Performed

### 1. Generated SSH Key Pair

```powershell
ssh-keygen -t ed25519 -f "D:\Articflow\ssh-keys\agentlink-hostinger-n8n" -C "agentlink-hostinger-n8n-vps"
```

**What this command does:**
- `-t ed25519`: Use ED25519 algorithm (modern, secure, fast)
- `-f`: Specify file path and name
- `-C`: Add a comment/label to identify the key
- When prompted for passphrase: Pressed Enter twice (no passphrase)

### 2. Key Files Created

Two files were created:

**Private Key** (`agentlink-hostinger-n8n`):
- Contains: Your secret authentication key
- Security: **NEVER SHARE THIS FILE**
- Size: 419 bytes

**Public Key** (`agentlink-hostinger-n8n.pub`):
- Contains: Public key that goes on the server
- Security: Safe to share with servers
- Size: 110 bytes

### 3. Added Public Key to Hostinger hPanel

**Steps followed:**
1. Logged into Hostinger hPanel: https://hpanel.hostinger.com
2. Navigated to **VPS** section
3. Selected the n8n VPS server
4. Clicked **Manage**
5. Went to **Settings** → **SSH keys** tab
6. Clicked **Add SSH key**
7. Filled in:
   - Name: `agentlink-hostinger-n8n`
   - SSH public key: Contents of `agentlink-hostinger-n8n.pub`
8. Clicked **Add SSH key**

### 4. Tested SSH Connection

**Connection command:**
```powershell
ssh -i "D:\Articflow\ssh-keys\agentlink-hostinger-n8n" root@72.62.64.72
```

**What this command does:**
- `ssh`: Secure Shell connection command
- `-i`: Specify which private key to use
- `root@72.62.64.72`: Username and server IP

**First connection:**
- System asks: "Are you sure you want to continue connecting (yes/no)?"
- Type: `yes` and press Enter
- Successfully connected without password!

## How SSH Key Authentication Works

### Traditional Password Method
```
You → Enter Password → Server checks password → Access granted/denied
```

### SSH Key Method
```
You → Send authentication request
Server → Sends challenge using your public key
Your private key → Solves challenge automatically
Server → Verifies solution → Access granted
```

### Why SSH Keys Are Better

1. **More Secure**: 256-bit encryption vs 8-12 character passwords
2. **No Password Typing**: Cannot be keylogged or shoulder-surfed
3. **Automated Access**: Scripts can connect without manual input
4. **Unique Per Device**: Each computer can have its own key
5. **Easy Revocation**: Remove public key from server to disable access

## Quick Reference Commands

### Connect to Hostinger VPS
```powershell
ssh -i "D:\Articflow\ssh-keys\agentlink-hostinger-n8n" root@72.62.64.72
```

### View Public Key
```powershell
Get-Content "D:\Articflow\ssh-keys\agentlink-hostinger-n8n.pub"
```

### Copy Public Key to Clipboard
```powershell
Get-Content "D:\Articflow\ssh-keys\agentlink-hostinger-n8n.pub" | Set-Clipboard
```

### Check Connection Status
```powershell
ssh -i "D:\Articflow\ssh-keys\agentlink-hostinger-n8n" root@72.62.64.72 "echo 'Connection successful'"
```

## Security Best Practices

### ✅ Do's

- Keep private key files in a secure location
- Use descriptive names for different keys
- Back up your private keys securely
- Use passphrases for keys on shared/portable devices
- Set correct file permissions (Windows handles this automatically)
- Remove old/unused keys from servers

### ❌ Don'ts

- Never share your private key file
- Never commit private keys to Git repositories
- Never email or message private keys
- Don't use the same key for everything
- Don't store keys in cloud folders without encryption

## Troubleshooting

### Permission Denied Errors

If you get "Permission denied (publickey)":

1. **Check key is added to hPanel**
   - Log into Hostinger hPanel
   - Verify key exists in SSH keys section

2. **Verify you're using correct username**
   - Try `root` or check VPS details in hPanel

3. **Check private key path is correct**
   ```powershell
   Test-Path "D:\Articflow\ssh-keys\agentlink-hostinger-n8n"
   ```

### Connection Timeout

If connection times out:

1. **Check VPS is running**
   - Log into hPanel and verify VPS status

2. **Verify firewall allows SSH (port 22)**
   - Check VPS firewall settings in hPanel

3. **Test with ping**
   ```powershell
   ping 72.62.64.72
   ```

### Bad Permissions Error

If you see "bad permissions" warning on Windows:

```powershell
icacls "D:\Articflow\ssh-keys\agentlink-hostinger-n8n" /inheritance:r
icacls "D:\Articflow\ssh-keys\agentlink-hostinger-n8n" /grant:r "kunal barve:R"
```

## Additional Resources

- **Hostinger SSH Keys Guide**: https://www.hostinger.com/tutorials/how-to-set-up-ssh-keys
- **Hostinger VPS Support**: https://support.hostinger.com/en/collections/944797-vps
- **ED25519 Algorithm**: Modern, secure, and faster than RSA
- **hPanel Dashboard**: https://hpanel.hostinger.com

---

**Document Created**: January 3, 2026  
**Last Updated**: January 3, 2026  
**Status**: ✅ SSH Access Configured and Tested
