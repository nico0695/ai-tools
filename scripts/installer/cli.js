const major = Number(process.versions.node.split('.')[0]);
if (major < 20) {
  console.error(`error: Node >= 20 required (found ${process.versions.node})`);
  process.exit(1);
}
const { main } = await import('./main.js');
process.exitCode = await main(process.argv.slice(2));
