# 🎯 VoiceConnect Pro - AI-Powered Call Center Platform

## 📋 Project Overview

VoiceConnect Pro is a comprehensive AI-powered call center platform designed for businesses that need practical automation without technical complexity. The system features intelligent tool chaining, SIM800C module integration, and business-focused AI functions that actually work for real business needs.

### 🌟 Key Features

- 🔗 **Visual Tool Chaining** - Connect AI tools in workflows with drag-and-drop interface
- 📱 **SIM800C Integration** - Real hardware SMS/voice communication with dual USB ports
- 🤖 **Business AI Functions** - Practical automation for customer follow-up, lead scoring, appointment scheduling
- 📊 **Real-time Dashboard** - Live monitoring with retro minimalistic design
- 💰 **Revenue Optimization** - Built-in subscription management and client onboarding
- 🎨 **Modern UI** - Retro minimalistic design with smooth animations

## 🏗️ System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Core API      │    │   SIM800C       │
│   (HTML/CSS/JS) │◄──►│   (FastAPI)     │◄──►│   Modules       │
│   Dashboard     │    │   Business AI   │    │   Hardware      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                       │                       │
        │                       │                       │
        ▼                       ▼                       ▼
   Port 12000              Port 8000              USB Ports
```

## 🚀 Quick Start

### 📋 Prerequisites

- **Python 3.8+** with pip
- **Node.js 16+** (optional, for advanced features)
- **SIM800C modules** with dual USB connections
- **Linux/Windows** system with USB ports

### 📥 Installation

#### 1. Clone Repository

```bash
git clone <repository-url>
cd Call-center-
```

#### 2. Install Python Dependencies

```bash
cd core-api
pip install -r requirements.txt
```

#### 3. Configure API Keys

Create `.env` file in project root:

```bash
# Core Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
DATABASE_URL=sqlite:///./ai_call_center.db

# SMS & Communication (Optional)
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_PHONE_NUMBER=your_twilio_number

# AI Services (Optional)
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Business APIs (Optional)
STRIPE_SECRET_KEY=your_stripe_key
SENDGRID_API_KEY=your_sendgrid_key

# Telegram Bot (Optional)
TELEGRAM_BOT_TOKEN=your_telegram_token
```

#### 4. Initialize Database

```bash
cd core-api
python init_db.py
```

#### 5. Start the System

```bash
# Start Core API
cd core-api
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# In another terminal, start frontend server
cd frontend
python -m http.server 12000
```

## 🖥️ Access the Platform

- **Main Website:** http://localhost:12000
- **Dashboard:** http://localhost:12000/dashboard.html
- **API Documentation:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

## 🔧 SIM800C Module Setup

### Hardware Configuration

1. **Connect SIM800C modules** with dual USB setup:
   - **Port 1:** AT commands + charging (e.g., `/dev/ttyUSB0`)
   - **Port 2:** Audio via USB sound card (e.g., `/dev/ttyUSB1`)

2. **Add modules via API:**

```bash
curl -X POST "http://localhost:8000/api/v1/modules" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "module_id": "sim800c_01",
    "at_port": "/dev/ttyUSB0",
    "audio_port": "/dev/ttyUSB1", 
    "gemini_api_key": "your_gemini_key_for_this_module"
  }'
```

3. **Test SMS sending:**

```bash
curl -X POST "http://localhost:8000/api/v1/modules/sim800c_01/sms" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "phone_number": "+1234567890",
    "message": "Test message from VoiceConnect Pro"
  }'
```

## 🤖 Business AI Tools

### Available Tools

1. **Customer Follow-up** - Automatically follow up with customers via SMS/call
2. **Lead Scoring** - Score leads based on engagement and profile
3. **Appointment Scheduler** - Schedule appointments automatically
4. **Quote Generator** - Generate customized quotes
5. **Sales Reports** - Automated reporting
6. **Customer Satisfaction** - Send surveys and analyze feedback

### Tool Chaining Example

Create a workflow that:
1. **Webhook Trigger** → Receives new lead
2. **Lead Scoring** → Scores the lead
3. **Condition Check** → High score vs low score
4. **Call Maker** → Calls high-value leads
5. **SMS Sender** → Sends SMS to lower-value leads

### Execute Tools via API

```bash
curl -X POST "http://localhost:8000/api/v1/tools/execute" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "tool_id": "customer_followup",
    "config": {
      "message_template": "Hello {name}! We wanted to follow up...",
      "follow_up_delay": 24
    },
    "context": {
      "customer_id": "cust_123",
      "type": "sms"
    }
  }'
```

## 📊 Dashboard Features

### Overview Section
- Real-time call statistics
- SMS delivery metrics
- Revenue tracking
- Live activity feed

### AI Tools Section
- Tool management and configuration
- Enable/disable tools
- Run tools manually
- View execution history

### Connections Section
- Visual workflow builder
- Drag-and-drop tool chaining
- Connection management
- Workflow validation

### Analytics Section
- Call volume charts
- Conversion funnels
- Revenue trends
- Tool performance metrics

### Settings Section
- SIM800C module management
- API key configuration
- Gemini keys per module
- System preferences

## 🔐 Authentication

### Default Login Credentials

- **Email:** `admin@voiceconnectpro.com`
- **Password:** `demo123`

### API Authentication

```bash
# Login to get token
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@voiceconnectpro.com",
    "password": "demo123"
  }'

# Use token in subsequent requests
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/tools"
```

## 🛠️ Configuration

### Business Tool Configuration

Each tool can be configured with specific parameters:

```python
# Customer Follow-up Configuration
{
    "message_template": "Hello {name}! We wanted to follow up on your recent inquiry.",
    "follow_up_delay": 24,  # hours
    "max_attempts": 3
}

# Lead Scoring Configuration  
{
    "scoring_factors": ["calls", "emails", "budget", "industry"],
    "threshold_high": 80,
    "threshold_medium": 60
}
```

### SIM800C Module Configuration

```python
# Module Settings
{
    "module_id": "sim800c_01",
    "at_port": "/dev/ttyUSB0",      # AT commands + charging
    "audio_port": "/dev/ttyUSB1",   # Audio via USB sound card
    "gemini_api_key": "module_specific_key",
    "timeout": 30,
    "retries": 3,
    "error_handling": "retry"
}
```

## 📈 Subscription Management

### Client Onboarding Process

1. **Client signs up** with company information
2. **30-minute consultation** to understand needs
3. **Automatic tool configuration** based on business type
4. **Ready-to-use setup** with pre-connected workflows

### Subscription Tiers

- **Starter ($99/month):** Up to 1,000 calls, 2 modules, basic analytics
- **Professional ($299/month):** Up to 5,000 calls, 5 modules, AI automation
- **Enterprise ($799/month):** Unlimited calls/modules, custom integrations

## 🔧 Troubleshooting

### Common Issues

#### 1. SIM800C Module Not Connecting

```bash
# Check USB ports
ls -la /dev/ttyUSB*

# Test AT commands manually
screen /dev/ttyUSB0 115200
AT
# Should respond with OK
```

#### 2. API Authentication Errors

```bash
# Verify token is valid
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/tools"
```

#### 3. Tool Execution Failures

Check logs:
```bash
tail -f core-api/server.log
```

#### 4. Frontend Connection Issues

Ensure both servers are running:
- Core API: http://localhost:8000
- Frontend: http://localhost:12000

### Performance Optimization

1. **Database optimization:** Use PostgreSQL for production
2. **Redis caching:** Enable Redis for better performance
3. **Load balancing:** Use nginx for multiple instances
4. **Monitoring:** Enable Prometheus metrics at `/metrics`

## 📚 API Documentation

### Core Endpoints

- `GET /api/v1/tools` - List available business tools
- `POST /api/v1/tools/execute` - Execute a business tool
- `GET /api/v1/modules` - List SIM800C modules
- `POST /api/v1/modules` - Add new SIM800C module
- `POST /api/v1/modules/{id}/sms` - Send SMS via module
- `POST /api/v1/modules/{id}/call` - Make call via module

### Webhook Integration

```bash
# Setup webhook for new leads
curl -X POST "http://localhost:8000/api/v1/webhooks" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-domain.com/webhook/leads",
    "events": ["lead.created", "lead.updated"],
    "workflow_id": "lead_processing_workflow"
  }'
```

## 🚀 Production Deployment

### Docker Deployment

```bash
# Build and run with Docker
docker-compose up -d
```

### Environment Variables

```bash
# Production settings
NODE_ENV=production
DATABASE_URL=postgresql://user:pass@localhost:5432/voiceconnect
REDIS_URL=redis://localhost:6379
WEBHOOK_BASE_URL=https://your-domain.com
```

### Security Considerations

1. **Change default passwords**
2. **Use HTTPS in production**
3. **Configure firewall rules**
4. **Regular security updates**
5. **API rate limiting**

## 📞 Support

### Getting Help

1. **Documentation:** Check this README and API docs
2. **Issues:** Create GitHub issues for bugs
3. **Community:** Join our Discord server
4. **Enterprise:** Contact sales for enterprise support

### Contributing

1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request

## 📄 License

This project is licensed under the MIT License. See LICENSE file for details.

## 🎯 Roadmap

### Upcoming Features

- [ ] **Mobile app** - React Native dashboard
- [ ] **Advanced analytics** - ML-powered insights  
- [ ] **CRM integrations** - Salesforce, HubSpot connectors
- [ ] **Voice AI** - Real-time conversation analysis
- [ ] **Multi-language** - International support
- [ ] **White-label** - Custom branding options

---

## 🏆 Project Status

**Status:** ✅ Production Ready  
**Version:** v2.0.0  
**Last Updated:** June 2025  

### Verified Functionality

- ✅ SIM800C hardware integration
- ✅ Business AI tool execution
- ✅ Visual workflow builder
- ✅ Real-time dashboard
- ✅ API authentication
- ✅ Subscription management
- ✅ Tool chaining system

**The platform is fully functional and ready for business use!** 🚀