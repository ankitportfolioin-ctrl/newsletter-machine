import express from 'express';
import dotenv from 'dotenv';
import { initializeDatabase } from './config/database';
import { configureSecurity, errorHandler, notFoundHandler, requestLogger, sanitizeInput } from './middleware/security';
import authRoutes from './routes/auth';
import nichesRoutes from './routes/niches';
import runsRoutes from './routes/runs';
import newslettersRoutes from './routes/newsletters';
import sourcesRoutes from './routes/sources';
import legalRoutes from './routes/legal';

// Load environment-specific config
const env = process.env.NODE_ENV || 'development';
dotenv.config({ path: `.env.${env}` });
dotenv.config(); // Fallback to .env

const app = express();
const PORT = process.env.PORT || 3001;

// Request logging
app.use(requestLogger);

// Security middleware
configureSecurity(app);

// Body parsing with size limit
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Input sanitization
app.use(sanitizeInput);

// Health check
app.get('/health', async (req, res) => {
  try {
    const { checkDatabaseHealth } = await import('./config/database');
    const dbHealth = await checkDatabaseHealth();
    
    res.json({
      status: 'ok',
      timestamp: new Date().toISOString(),
      environment: process.env.NODE_ENV || 'development',
      database: dbHealth,
      uptime: process.uptime(),
      memory: process.memoryUsage(),
    });
  } catch (error) {
    res.status(503).json({
      status: 'error',
      timestamp: new Date().toISOString(),
      error: error instanceof Error ? error.message : 'Unknown error',
    });
  }
});

// API routes
app.use('/api/auth', authRoutes);
app.use('/api/niches', nichesRoutes);
app.use('/api/runs', runsRoutes);
app.use('/api/newsletters', newslettersRoutes);
app.use('/api/sources', sourcesRoutes);
app.use('/api/legal', legalRoutes);

// 404 handler
app.use(notFoundHandler);

// Error handling middleware
app.use(errorHandler);

// Start server
async function start() {
  try {
    // Initialize database
    await initializeDatabase();
    console.log('Database initialized');

    // Start server
    const server = app.listen(PORT, () => {
      console.log(`Server running on port ${PORT}`);
      console.log(`Environment: ${process.env.NODE_ENV || 'development'}`);
      console.log(`Health check: http://localhost:${PORT}/health`);
    });

    // Graceful shutdown
    const gracefulShutdown = async (signal: string) => {
      console.log(`\n${signal} received. Starting graceful shutdown...`);
      
      server.close(async () => {
        console.log('HTTP server closed');
        
        const { closeDatabase } = await import('./config/database');
        await closeDatabase();
        
        console.log('Graceful shutdown complete');
        process.exit(0);
      });

      // Force shutdown after 10 seconds
      setTimeout(() => {
        console.error('Could not close connections in time, forcefully shutting down');
        process.exit(1);
      }, 10000);
    };

    process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));
    process.on('SIGINT', () => gracefulShutdown('SIGINT'));

  } catch (error) {
    console.error('Failed to start server:', error);
    process.exit(1);
  }
}

start();

export default app;
