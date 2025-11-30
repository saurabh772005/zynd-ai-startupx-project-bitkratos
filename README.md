# n8n-nodes-zyndai

Custom n8n nodes for integrating with the ZyndAI network and Web3 payment protocols (X402).

## Overview

This package provides custom n8n nodes that enable:
- **Zynd Agent Search**: Discover agents by capabilities on the ZyndAI network
- **Zynd Agent Publisher**: Publish your n8n workflows as agents to the ZyndAI registry
- **X402 Webhook**: Webhook node with built-in Web3 payment verification using the x402 protocol
- **X402 Respond to Webhook**: Custom response node for X402 webhooks with payment settlement
- **X402 HTTP Request**: Make HTTP requests with automatic Web3 payment using the x402-fetch protocol

## Quick Start

Get started in 2 minutes with the automated development setup:

```bash
# 1. Install prerequisites
npm install -g pnpm
# Make sure ngrok is installed and authenticated (see Prerequisites)

# 2. Clone and setup
git clone <repository-url>
cd n8n-nodes-zyndai
chmod +x run-manual.sh

# 3. Run!
./run-manual.sh
```

Your n8n instance with custom nodes will be running with auto-reload enabled. The ngrok public URL will be displayed in the terminal.

For production deployment, use the [Docker method](#method-1-docker-recommended-for-production).

## Features

- Web3 wallet integration using Viem
- X402 payment protocol support for monetizing webhooks and APIs
- X402 HTTP client for accessing paid endpoints
- Multi-network support (Ethereum, Base, Polygon, Arbitrum, Optimism, BSC, Avalanche, and testnets)
- Synchronous and asynchronous payment settlement modes
- ZyndAI agent registry integration
- DID-based wallet generation from seed phrases (BIP-39/BIP-44)

## Prerequisites

- **Node.js** (v18 or higher recommended) and npm/pnpm
- **Docker** and **Docker Compose** (for Docker installation method)
- **ngrok** (Must be installed on host and authenticated with authtoken)
- **n8n** (for manual installation)
- **jq** (for run.sh Docker script - to parse ngrok JSON output)
- **nodemon** (optional, for run-manual.sh script - auto-reload on changes)

## Installation

There are three methods to run this project. Choose based on your needs:

| Method | Best For | Auto-reload | Setup Time | Complexity |
|--------|----------|-------------|------------|------------|
| [run-manual.sh](#method-2-automated-manual-installation-recommended-for-development) | Development | ✅ Yes | ~2 min | Low |
| [Docker](#method-1-docker-recommended-for-production) | Production | ❌ No | ~3 min | Medium |
| [Manual](#method-3-manual-installation) | Full Control | ⚙️ Optional | ~5 min | High |

### Method 1: Docker (Recommended for Production)

This method uses Docker Compose with ngrok for automatic public URL setup.

#### Step 1: Configure Ngrok

The `run.sh` script relies on `ngrok` to create a public tunnel. You must have ngrok installed and authenticated.

1.  **Install ngrok**: [https://ngrok.com/download](https://ngrok.com/download)
2.  **Connect your account**:
    ```bash
    ngrok config add-authtoken <YOUR_AUTH_TOKEN>
    ```
    (Get your token from the [ngrok dashboard](https://dashboard.ngrok.com/get-started/your-authtoken))

#### Step 2: Start the Infrastructure

```bash
./run.sh
```

This script will:
1. Start ngrok tunnel on port 5678
2. Automatically configure environment variables (.env file)
3. Build and start n8n in Docker with the custom nodes pre-installed
4. Make your n8n instance publicly accessible via ngrok URL


#### Step 3: Stop the Infrastructure

```bash
./stop.sh
```

This will stop and clean up the ngrok process.

### Method 2: Automated Manual Installation (Recommended for Development)

This method uses the `run-manual.sh` script to automatically set up everything for local development with hot-reload support.

#### Features:
- Automatic ngrok tunnel setup
- Environment variable configuration
- Global n8n installation
- Package build and linking
- Auto-reload on file changes using nodemon

#### Prerequisites:
- ngrok installed and authenticated
- pnpm installed (`npm install -g pnpm`)

#### Steps:

**1. Make the script executable:**
```bash
chmod +x run-manual.sh
```

**2. Run the script:**
```bash
./run-manual.sh
```

The script will automatically:
1. Start ngrok tunnel on port 5678
2. Extract and export the public ngrok URL
3. Install n8n and nodemon globally
4. Install project dependencies using pnpm
5. Build the custom nodes
6. Link the package globally
7. Set up the `~/.n8n/custom` directory
8. Launch n8n with auto-reload on changes

**3. Access n8n:**
- Your n8n instance will be available at the ngrok URL displayed in the terminal
- Local access: `http://localhost:5678`

**4. Development workflow:**
- The script uses nodemon to watch the `dist/` folder
- Any changes you make will trigger an automatic rebuild and n8n restart
- For active development, run `npm run build:watch` in a separate terminal to auto-rebuild on TypeScript changes

**5. Stop the services:**
Press `Ctrl+C` to stop n8n and manually stop ngrok:
```bash
pkill ngrok
```

### Method 3: Manual Installation

For complete manual control without automation scripts.

#### Step 1: Install n8n globally

```bash
npm install -g n8n
```

#### Step 2: Build the package

```bash
npm install
npm run build
```

#### Step 3: Link the package globally

```bash
npm link
```

This makes `n8n-nodes-zyndai` available as a global npm package.

#### Step 4: Create custom nodes directory

The location depends on your operating system:

**Linux/macOS:**
```bash
mkdir -p ~/.n8n/custom
cd ~/.n8n/custom
```

**Windows (PowerShell):**
```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.n8n\custom"
cd "$env:USERPROFILE\.n8n\custom"
```

**Windows (Command Prompt):**
```cmd
mkdir %USERPROFILE%\.n8n\custom
cd %USERPROFILE%\.n8n\custom
```

#### Step 5: Link the package in the custom directory

```bash
npm link n8n-nodes-zyndai
```

This creates a symlink to your globally linked package.

#### Step 6: Start n8n

```bash
npx n8n start
```

Your custom nodes will now be available in n8n at `http://localhost:5678`

## Configuration

### Environment Variables

Create a `.env` file in the project root. Use `.env.example` as a template:

```bash
cp .env.example .env
```

#### Required Environment Variables:

```env
# Database Configuration
DB_TYPE=sqlite

# N8N Encryption Key
# Get from existing n8n: docker exec -it <container_name> printenv N8N_ENCRYPTION_KEY
# Or generate a new one for fresh installations
N8N_ENCRYPTION_KEY=your_encryption_key_here

# Logging
N8N_LOG_LEVEL=debug
N8N_LOG_OUTPUT=console
CODE_ENABLE_STDOUT=true

# Network Configuration (auto-generated by run.sh for Docker method)
N8N_HOST=
N8N_EDITOR_BASE_URL=
N8N_PUBLIC_API_BASE_URL=
WEBHOOK_URL=
N8N_PORT=5678
N8N_PROTOCOL=https
```

**Note**: For the Docker method, network variables are automatically configured by `run.sh`. For manual installation, configure these according to your setup.

### Credentials Setup in n8n

After starting n8n, configure the following credentials:

#### ZyndAI API Credentials
1. Navigate to **Settings > Credentials** in n8n
2. Create **ZyndAI API** credential:
   - **API URL**: `https://registry.zynd.ai` (default)
   - **Zynd API Key**: Get from [https://dashboard.zynd.ai](https://dashboard.zynd.ai)
   - **N8N API Key**: Generate from n8n **Settings > API**

#### Web3 Wallet Credentials (Optional)
Required for Web3-enabled features. Configure as needed for your use case.

## Available Nodes

### 1. Zynd Agent Search

Search for agents by capabilities on the ZyndAI network.

**Parameters:**
- **Agent Keyword**: Search by name, description, etc.
- **Capabilities**: Multi-select capabilities filter

**Use Case**: Discover and integrate existing agents from the ZyndAI network into your workflows.

### 2. Zynd Agent Publisher

Publish your n8n workflows as agents to the ZyndAI registry.

**Requirements:**
- ZyndAI API credentials configured
- Workflow containing a webhook node

**Use Case**: Share your n8n workflows as reusable agents on the ZyndAI network.

### 3. X402 Webhook

Webhook node with integrated Web3 payment verification using the x402 protocol.

**Parameters:**
- **HTTP Method**: GET, POST, PUT, DELETE, PATCH
- **Path**: Webhook endpoint path
- **Response Mode**:
  - **On Received**: Returns data immediately
  - **Response Node**: Use X402 Respond to Webhook node
- **Facilitator URL**: x402 payment facilitator endpoint
- **Server Wallet Address**: Ethereum address to receive payments (0x...)
- **Price**: Payment amount (e.g., `$0.01`)
- **Network**: Blockchain network selection

**Supported Networks:**
- Base
- Base Sepolia (Testnet)
- Ethereum
- Ethereum Sepolia (Testnet)
- Polygon
- Arbitrum
- Arbitrum Sepolia (Testnet)
- Optimism

**Options:**
- **Require Payment**: Toggle payment requirement (default: true)
- **Description**: Payment description
- **MIME Type**: Response content type (default: `application/json`)
- **Max Timeout Seconds**: Payment validity duration (default: 60)
- **Include Payment Details**: Add payment info to workflow data
- **Settlement Mode**:
  - **Synchronous**: Settle payment before responding
  - **Asynchronous**: Settle payment in background

**Use Case**: Monetize your webhooks by requiring Web3 payments before processing requests.

### 4. X402 Respond to Webhook

Custom response node for X402 webhooks with payment header support.

**Parameters:**
- **Respond With**: Choose response format (JSON, Binary, All Items, etc.)
- **Response Code**: HTTP status code
- **Response Headers**: Custom headers including X402 payment headers

**Use Case**: Control response behavior for X402 webhooks, especially when using "Response Node" mode.

### 5. X402 HTTP Request

Make HTTP requests with automatic Web3 payment using the x402-fetch protocol. This node acts as a buyer/client that pays to access X402-protected endpoints.

**Parameters:**
- **Method**: HTTP method (GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS)
- **URL**: The endpoint URL to call (must support X402 protocol)
- **Authentication**: Optional authentication (None, Basic Auth, Header Auth, OAuth2, etc.)
- **Send Query Parameters**: Add URL query parameters
- **Send Headers**: Add custom HTTP headers
- **Send Body**: Request body (JSON, Form Data, etc.)

**Web3 Payment Configuration:**
- **Agent Seed Phrase**: BIP-39 seed phrase for the wallet that will pay (12-24 words)
- **Network**: Blockchain network to use for payment
  - Base
  - Base Sepolia (Testnet)
  - Ethereum Mainnet
  - Ethereum Sepolia (Testnet)
  - Polygon
  - Polygon Mumbai (Testnet)
  - Optimism
  - Optimism Sepolia (Testnet)
  - Arbitrum
  - Arbitrum Sepolia (Testnet)
  - Avalanche
  - Avalanche Fuji (Testnet)
  - BSC (Binance Smart Chain)
  - BSC Testnet

**Features:**
- Automatic wallet generation from seed phrase using BIP-39/BIP-44
- Seamless payment handling through x402-fetch
- Standard HTTP request capabilities with payment layer
- Full network support for major EVM chains

**Use Case**: Access monetized APIs and webhooks that require X402 payment. Perfect for integrating with X402 Webhook nodes or other x402-protected services.

## X402 Payment Flow

The package provides both seller and buyer nodes for the X402 payment protocol:

**Seller Side (Receive Payments):**
- Use **X402 Webhook** to create paid API endpoints
- Clients must pay to access your webhook
- Payments are verified and settled automatically
- Use **X402 Respond to Webhook** for custom responses

**Buyer Side (Make Payments):**
- Use **X402 HTTP Request** to call paid endpoints
- Automatically handles payment from your wallet
- Supports all major EVM networks
- Seamless integration with standard HTTP workflows

**Example Use Case:**
1. Service A publishes a paid AI model API using **X402 Webhook**
2. Service B calls that API using **X402 HTTP Request**
3. Payment flows automatically from Service B's wallet to Service A's wallet
4. Both services continue their workflows seamlessly

## Development Scripts

| Script                | Description                                                      |
| --------------------- | ---------------------------------------------------------------- |
| `npm run build`       | Compile TypeScript to JavaScript                                 |
| `npm run build:watch` | Build in watch mode (auto-rebuild on changes)                    |
| `npm run dev`         | TypeScript watch mode (use with nodemon for hot reload)          |
| `npm run lint`        | Check code for errors and style issues                           |
| `npm run lint:fix`    | Automatically fix linting issues                                 |
| `./run.sh`            | Docker setup with ngrok (production-like environment)            |
| `./run-manual.sh`     | Automated manual install with auto-reload (development)          |
| `./stop.sh`           | Stop Docker services and ngrok                                   |

### Development Workflow

**For active development with hot-reload:**

1. **Option A - Using run-manual.sh (Easiest):**
   ```bash
   ./run-manual.sh
   ```
   This handles everything automatically including auto-reload.

2. **Option B - Manual setup with watch mode:**

   Terminal 1 - Build watcher:
   ```bash
   npm run build:watch
   ```

   Terminal 2 - n8n with auto-reload:
   ```bash
   npx nodemon --watch ./dist --exec "n8n start"
   ```

**For production-like testing:**
```bash
./run.sh  # Docker with ngrok
```

## Project Structure

```
n8n-nodes-zyndai/
├── nodes/
│   └── Zynd/
│       ├── SearchAgent.node.ts          # Zynd agent search node
│       ├── AgentPublisher.node.ts       # Zynd agent publisher node
│       ├── X402Webhook.node.ts          # X402 webhook with payments (seller)
│       ├── X402RespondToWebhook.node.ts # X402 response node
│       ├── X402HttpRequest.node.ts      # X402 HTTP request node (buyer)
│       └── utils/                       # Utility functions
│           ├── binary.ts                # Binary data handling
│           ├── output.ts                # Output configuration
│           └── utilities.ts             # Helper functions
├── credentials/
│   ├── ZyndAIAPI.credentials.ts         # ZyndAI API credentials
│   └── Web3.credentials.ts              # Web3 wallet credentials
├── icons/                               # Node icons
│   └── zynd.svg                        # ZyndAI logo
├── build/                               # Build scripts
├── dist/                                # Compiled JavaScript (auto-generated)
├── data_n8n/                            # n8n data directory (Docker volumes)
├── Dockerfile                           # Docker build configuration
├── docker-compose.yaml                  # Docker Compose setup
├── run.sh                               # Docker start script with ngrok
├── run-manual.sh                        # Manual install script with auto-reload
├── stop.sh                              # Docker stop script
├── .env.example                         # Environment template
├── package.json                         # Package configuration
├── gulpfile.js                          # Gulp build tasks
├── tsconfig.json                        # TypeScript configuration
└── README.md                            # This file
```

## Key Dependencies

- **viem** (^2.39.3): Ethereum library for Web3 functionality
- **x402** (^0.7.3): Payment protocol implementation (webhook seller side)
- **x402-fetch** (^0.7.3): Payment-enabled fetch wrapper (HTTP client buyer side)
- **lodash** (^4.17.21): Utility functions

## Troubleshooting

### Docker Method Issues

**Ngrok URL not found:**
- Ensure ngrok is installed: `ngrok version`
- Check if port 4040 is available (ngrok web interface)
- Review ngrok.log if it exists (created temporarily during startup)

**Docker build fails:**
- Ensure Docker daemon is running
- Try rebuilding: `docker compose build --no-cache`
- Check Docker logs: `docker compose logs`

**Container won't start:**
- Verify `.env` file exists and is properly configured
- Check port 5678 is not already in use
- Ensure sufficient disk space for Docker volumes

### run-manual.sh Script Issues

**Script fails to start ngrok:**
- Verify ngrok is installed: `ngrok version`
- Check ngrok authentication: `ngrok config check`
- Ensure port 5678 is not already in use
- Stop existing ngrok processes: `pkill ngrok`

**"Could not fetch ngrok public URL" error:**
- Wait a few more seconds and check `http://127.0.0.1:4040/status`
- Ensure no firewall is blocking ngrok
- Check ngrok.log for errors: `cat ngrok.log`

**pnpm not found:**
- Install pnpm globally: `npm install -g pnpm`
- Or modify the script to use `npm` instead of `pnpm`

**n8n won't auto-reload:**
- Ensure nodemon is installed: `npm list -g nodemon`
- Check that `dist/` folder exists
- Verify build is creating files in `dist/`
- Try manual restart: Kill n8n (Ctrl+C) and run `npx n8n start`

**Permission denied on run-manual.sh:**
- Make script executable: `chmod +x run-manual.sh`

### Manual Installation Issues

**Nodes not appearing in n8n:**
1. Verify build completed successfully: `npm run build`
2. Check `dist/` folder exists and contains compiled files
3. Ensure `npm link` was successful (no errors)
4. Verify symlink exists: `ls -la ~/.n8n/custom/`
5. Restart n8n after building: `npx n8n start`
6. Check package name in `package.json` is `n8n-nodes-zyndai`

**Import/Build errors:**
- Run `npm install` to ensure all dependencies are installed
- Check Node.js version: `node --version` (v18+ recommended)
- Clear node_modules and reinstall: `rm -rf node_modules && npm install`
- Clear TypeScript cache: `rm -rf dist/ && npm run build`

**Credential configuration errors:**
- Verify credentials are properly saved in n8n
- Check API keys are valid and not expired
- Ensure correct API URL format (include https://)
- Generate new N8N API key if needed

**Webhook payment errors:**
- Verify facilitator URL is accessible
- Check wallet address format (must start with 0x)
- Ensure network matches the asset being used
- Verify sufficient funds in payer wallet for testnet

**"Cannot find module" errors:**
- Ensure all peer dependencies are installed
- Check n8n-workflow version compatibility
- Run `npm install` again
- Verify symlink is correctly pointing to package

### Development Issues

**Hot reload not working:**
- Use `npm run build:watch` for auto-rebuild
- Restart n8n if changes don't appear
- Check for TypeScript compilation errors

**Linting errors:**
- Run `npm run lint:fix` to auto-fix common issues
- Check [n8n node development guidelines](https://docs.n8n.io/integrations/creating-nodes/)

## Resources

- **[ZyndAI Documentation](https://docs.zynd.ai)** - ZyndAI platform documentation
- **[ZyndAI Dashboard](https://dashboard.zynd.ai)** - Get API keys and manage agents
- **[n8n Documentation](https://docs.n8n.io)** - n8n workflow automation docs
- **[n8n Node Development](https://docs.n8n.io/integrations/creating-nodes/)** - Guide to building custom nodes
- **[X402 Protocol](https://x402.org)** - Web3 payment protocol documentation
- **[Viem Documentation](https://viem.sh)** - Ethereum library documentation

## Support

For issues and questions:
- **ZyndAI Issues**: Contact via [ZyndAI Dashboard](https://dashboard.zynd.ai)
- **n8n Issues**: Visit [n8n Community Forum](https://community.n8n.io/)
- **Project Issues**: Open an issue on the repository
- **Email**: swapnilshinde9382@gmail.com

## Author

**Swapnil Shinde**
- Email: swapnilshinde9382@gmail.com
- Package: n8n-nodes-zyndai

## License

MIT
