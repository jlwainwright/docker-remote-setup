# Token Vending Portal - Environment Configuration Guide

This document explains the environment variables used to configure the Token Vending Portal.

## Configuration File: `.env`

### Required Variables

#### CyberVendIT Credentials
```bash
CYBERVENDIT_USERNAME=your_username
CYBERVENDIT_PASSWORD=your_password
```
- Your login credentials for the CyberVendIT website
- Required for the Playwright automation to log into the site

#### Database
```bash
DATABASE_URL=sqlite+aiosqlite:///./cyberzapvend.db
```
- Database connection string for storing transactions and property data

### Optional Configuration Variables

#### Demo Mode
```bash
CYBERVENDIT_DEMO_MODE=true
```
- **`true`**: Safe testing mode - returns "DEMO_TOKEN_12345" without generating real tokens
- **`false`**: Production mode - generates actual tokens on the CyberVendIT website
- **Default**: `false`
- **Recommended for development**: `true`

#### Browser Headless Mode
```bash
CYBERVENDIT_HEADLESS=true
```
- **`true`**: Run browser automation in background (headless mode)
- **`false`**: Show browser window during automation (useful for debugging)
- **Default**: `true`
- **Recommended for production**: `true`
- **Recommended for debugging**: `false`

### Valid Boolean Values

All boolean environment variables accept these values (case-insensitive):
- **True**: `true`, `1`, `yes`, `y`, `t`
- **False**: `false`, `0`, `no`, `n`, `f`

## Configuration Examples

### Development Environment
```bash
CYBERVENDIT_USERNAME=your_username
CYBERVENDIT_PASSWORD=your_password
CYBERVENDIT_DEMO_MODE=true      # Safe testing
CYBERVENDIT_HEADLESS=false      # Visible browser for debugging
DATABASE_URL=sqlite+aiosqlite:///./cyberzapvend.db
```

### Production Environment
```bash
CYBERVENDIT_USERNAME=your_username
CYBERVENDIT_PASSWORD=your_password
CYBERVENDIT_DEMO_MODE=false     # Generate real tokens
CYBERVENDIT_HEADLESS=true       # Background execution
DATABASE_URL=sqlite+aiosqlite:///./cyberzapvend.db
```

### Debugging Environment
```bash
CYBERVENDIT_USERNAME=your_username
CYBERVENDIT_PASSWORD=your_password
CYBERVENDIT_DEMO_MODE=true      # Safe testing
CYBERVENDIT_HEADLESS=false      # Watch browser automation
DATABASE_URL=sqlite+aiosqlite:///./cyberzapvend.db
```

## Usage Notes

1. **Demo Mode**: Always test with `CYBERVENDIT_DEMO_MODE=true` first to ensure everything works without generating real tokens.

2. **Headless Debugging**: Set `CYBERVENDIT_HEADLESS=false` if you need to see what the browser automation is doing (useful for troubleshooting selectors or login issues).

3. **Production Deployment**: Use `CYBERVENDIT_DEMO_MODE=false` and `CYBERVENDIT_HEADLESS=true` for production deployments.

4. **Security**: Never commit your actual credentials to version control. Keep the `.env` file in your `.gitignore`.

## Testing Configuration Changes

After changing environment variables, restart the backend server for changes to take effect:

```bash
# Stop the current server (Ctrl+C)
# Then restart:
uvicorn backend.main:app --host 0.0.0.0 --port 8001 --reload
```

## Troubleshooting

- **"CyberVendIT credentials not configured"**: Check that `CYBERVENDIT_USERNAME` and `CYBERVENDIT_PASSWORD` are set
- **Browser automation failing**: Try setting `CYBERVENDIT_HEADLESS=false` to see what's happening
- **"Amount too low to cover vending fee"**: The amount must be higher than the property's vending fee (usually R10)
