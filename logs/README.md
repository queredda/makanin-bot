# Logs Directory

This directory contains example log files for the Makanin bot system.

## Log Files

### 1. `example_agent.log`

Contains typical agent execution logs showing:

- User message processing
- Tool execution workflows
- Food search workflows
- Conversation handling
- Success and error scenarios

### 2. `example_performance.log`

Contains performance monitoring logs with:

- Tool execution timing
- Message processing duration
- Success/failure rates
- Performance statistics and averages
- Bottleneck identification

### 3. `example_error.log`

Contains error logs demonstrating:

- API failures (Gemini, TikTok, Google Maps)
- Connection issues (Redis)
- Validation errors
- System exceptions
- Error categorization and summaries

## Log Format

All logs follow this format:

```
TIMESTAMP - LEVEL - [COMPONENT] Message
```

### Log Levels:

- `INFO`: General information about system operations
- `WARNING`: Non-critical issues that don't stop execution
- `ERROR`: Errors that affect functionality but don't crash system
- `CRITICAL`: Serious errors that may cause system failure
- `PERF`: Performance monitoring data

### Components:

- `Agent`: Main agent processing logic
- `NLU Tool`: Natural language understanding
- `TikTok Search`: TikTok content search
- `Place Extraction`: Restaurant name extraction
- `Location Resolution`: Google Maps integration
- `Weather Tool`: Weather information
- `Conversation Tool`: Chat response generation
- `Context Manager`: Session and memory management
- `Tool Registry/Executor`: Tool management system
- `Redis Connection`: Database connectivity

## Usage Examples

### Viewing Recent Activity

```bash
tail -f logs/example_agent.log
```

### Filtering Errors Only

```bash
grep "ERROR" logs/example_error.log
```

### Performance Analysis

```bash
grep "PERF" logs/example_performance.log
```

### Searching Specific User Activity

```bash
grep "user123" logs/example_agent.log
```

## Log Rotation

For production deployment, consider implementing log rotation:

```bash
# Example logrotate configuration
/path/to/makanin-bot/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 user user
}
```

## Monitoring Integration

These logs can be integrated with monitoring tools:

- **ELK Stack** (Elasticsearch, Logstash, Kibana)
- **Grafana Loki**
- **Datadog**
- **Splunk**
- **CloudWatch** (AWS)

## Debugging Tips

1. **API Issues**: Look for timeout and authentication errors
2. **Performance**: Check PERF logs for slow tool execution
3. **User Issues**: Search by user ID to trace specific sessions
4. **System Health**: Monitor ERROR and CRITICAL levels
5. **Resource Usage**: Watch for memory and connection warnings