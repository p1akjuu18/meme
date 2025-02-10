module.exports = {
  apps: [
    {
      name: 'data_update_scheduler',
      script: 'real_time_running/data_update_scheduler.py',
      interpreter: 'python',
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      error_file: 'logs/data_update_error.log',
      out_file: 'logs/data_update_out.log',
      merge_logs: true,
      time: true,
      env: {
        NODE_ENV: 'development'
      }
    },
    {
      name: 'analysis_scheduler',
      script: 'real_time_running/analysis_scheduler.py',
      interpreter: 'python',
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      error_file: 'logs/analysis_scheduler_error.log',
      out_file: 'logs/analysis_scheduler_out.log',
      merge_logs: true,
      time: true,
      env: {
        NODE_ENV: 'development'
      }
    },
    {
      name: 'real_time_update',
      script: 'real_time_running/real_time_update.py',
      interpreter: 'python',
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      error_file: 'logs/real_time_update_error.log',
      out_file: 'logs/real_time_update_out.log',
      merge_logs: true,
      time: true,
      env: {
        NODE_ENV: 'development'
      }
    },
    {
      name: 'telegram_price_alert',
      script: 'telegram_price_alert.py',
      interpreter: 'python',
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      error_file: 'logs/telegram_alert_error.log',
      out_file: 'logs/telegram_alert_out.log',
      merge_logs: true,
      time: true,
      env: {
        NODE_ENV: 'development'
      }
    }
  ]
}; 