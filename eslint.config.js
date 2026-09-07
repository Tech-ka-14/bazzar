// ESLint 9 flat config for the Bazzar renderer + Electron shell.
import js from '@eslint/js';
import globals from 'globals';
import reactPlugin from 'eslint-plugin-react';

export default [
  {
    ignores: ['dist/**', 'release/**', 'build/**', 'node_modules/**', 'coverage/**'],
  },
  js.configs.recommended,
  {
    files: ['src/**/*.{js,jsx}', 'vite.config.js', 'vitest.config.js'],
    plugins: { react: reactPlugin },
    languageOptions: {
      parserOptions: { ecmaFeatures: { jsx: true } },
      globals: { ...globals.browser },
    },
    settings: { react: { version: 'detect' } },
    rules: {
      ...reactPlugin.configs.recommended.rules,
      'react/jsx-uses-vars': 'error',
      'react/prop-types': 'off',
      'react/react-in-jsx-scope': 'off',
    },
  },
  {
    // Node ESM config files (package.json has "type": "module").
    files: ['postcss.config.js', 'tailwind.config.js'],
    languageOptions: {
      sourceType: 'module',
      globals: { ...globals.node },
    },
  },
  {
    files: ['electron/**/*.cjs', 'scripts/**/*.cjs'],
    languageOptions: {
      sourceType: 'commonjs',
      globals: { ...globals.node },
    },
  },
  {
    files: ['src/__tests__/**/*.{js,jsx}'],
    languageOptions: {
      globals: { ...globals.node },
    },
  },
];
