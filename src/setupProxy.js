const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function (app) {
  // Proxy API requests
  app.use(
    '/api',
    createProxyMiddleware({
      target: 'http://localhost:4142',
      changeOrigin: true,
    }),
  );

  // Proxy GraphQL requests
  app.use(
    '/graphql',
    createProxyMiddleware({
      target: 'http://localhost:4142',
      changeOrigin: true,
    }),
  );
};
