const assert = require('assert');
const path = require('path');

// Mock child_process modules
const child_process = require('child_process');

let spawnSyncCalled = false;
let spawnSyncArgs = null;

// Save original methods
const originalExecSync = child_process.execSync;
const originalSpawnSync = child_process.spawnSync;

// Mock execSync to bypass version check and installation check
child_process.execSync = function(cmd, options) {
  if (cmd.includes('--version') || cmd.includes('import click_to_mcp')) {
    return Buffer.from('mocked');
  }
  return originalExecSync(cmd, options);
};

child_process.spawnSync = function(cmd, args, options) {
  spawnSyncCalled = true;
  spawnSyncArgs = { cmd, args, options };
  return { status: 0 };
};

// Set up fake process.argv
const originalArgv = process.argv;
process.argv = ['node', 'cli.js', '--help', 'arg with spaces', 'arg;echo INJECTED'];

// Intercept process.exit
let exitCode = null;
const originalExit = process.exit;
process.exit = function(code) {
  exitCode = code;
};

try {
  // Load cli.js
  require('../cli.js');

  // Assert spawnSync was called correctly
  assert.strictEqual(spawnSyncCalled, true, "spawnSync should have been called");
  assert.ok(spawnSyncArgs.args.includes('--help'), "Arguments should be passed to spawnSync");
  assert.ok(spawnSyncArgs.args.includes('arg with spaces'), "Spaces should be preserved in arguments");
  assert.ok(spawnSyncArgs.args.includes('arg;echo INJECTED'), "Semicolons should be preserved as literal args");
  
  // Verify that the command and standard click-to-mcp entrypoint pattern are correct
  assert.strictEqual(spawnSyncArgs.args[0], '-m');
  assert.strictEqual(spawnSyncArgs.args[1], 'click_to_mcp.cli');
  
  console.log("cli.js wrapper test passed successfully.");
} catch (e) {
  console.error("cli.js wrapper test failed:", e);
  process.exit(1);
}

// Clean require cache for the next test
delete require.cache[require.resolve('../cli.js')];

spawnSyncCalled = false;
spawnSyncArgs = null;
process.argv = ['node', 'cli-demo.js', '--help', 'arg with spaces', 'arg;echo INJECTED'];

try {
  // Load cli-demo.js
  require('../cli-demo.js');

  // Assert spawnSync was called correctly
  assert.strictEqual(spawnSyncCalled, true, "spawnSync should have been called for cli-demo.js");
  assert.ok(spawnSyncArgs.args.includes('--help'), "Arguments should be passed to spawnSync");
  assert.ok(spawnSyncArgs.args.includes('arg with spaces'), "Spaces should be preserved in arguments");
  assert.ok(spawnSyncArgs.args.includes('arg;echo INJECTED'), "Semicolons should be preserved as literal args");
  
  // Verify that the command and demo entrypoint pattern are correct
  assert.strictEqual(spawnSyncArgs.args[0], '-m');
  assert.strictEqual(spawnSyncArgs.args[1], 'click_to_mcp.demo');
  
  console.log("cli-demo.js wrapper test passed successfully.");
} catch (e) {
  console.error("cli-demo.js wrapper test failed:", e);
  process.exit(1);
} finally {
  // Restore original
  child_process.execSync = originalExecSync;
  child_process.spawnSync = originalSpawnSync;
  process.argv = originalArgv;
  process.exit = originalExit;
}
