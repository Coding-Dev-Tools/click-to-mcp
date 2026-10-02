#!/usr/bin/env node
// npm wrapper for click-to-mcp Python CLI
// Installs the Python package and runs the CLI
const { execSync, spawnSync } = require('child_process');
const path = require('path');

function getPythonCommand() {
  const commands = ['python3', 'python'];
  for (const cmd of commands) {
    try {
      execSync(`${cmd} --version`, { stdio: 'ignore' });
      return cmd;
    } catch (e) {
      continue;
    }
  }
  console.error('Error: Python 3 is required but not found. Install it from https://python.org');
  process.exit(1);
}

function ensureInstalled() {
  const pythonCmd = getPythonCommand();
  try {
    execSync(`${pythonCmd} -c "import click_to_mcp"`, { stdio: 'ignore' });
  } catch (e) {
    console.log('Installing click-to-mcp Python package...');
    execSync(`${pythonCmd} -m pip install click-to-mcp`, { stdio: 'inherit' });
  }
}

const pythonCmd = getPythonCommand();
ensureInstalled();

const result = spawnSync(pythonCmd, ['-m', 'click_to_mcp.cli', ...process.argv.slice(2)], {
  stdio: 'inherit',
  env: { ...process.env }
});
process.exit(result.status ?? 0);

