module.exports = {
  testEnvironment: 'node',
  testMatch: ['**/*.test.js'],
  collectCoverageFrom: [
    'app/static/js/**/*.js',
    '!app/static/js/**/*.test.js'
  ],
  coverageDirectory: 'coverage',
  verbose: true
};
