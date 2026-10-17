// Safe compatibility entry point. Do not regenerate the old transparent-logo set.
// The release icon pipeline is explicitly opt-in and uses scripts/build-appstore-icons.py.
import { spawnSync } from "node:child_process";
if (!process.argv.includes("--refresh-app-store")) {
  console.error("Archived: old simple-icons generator disabled to protect official App Store icon artwork.");
  console.error("To explicitly update from Apple, run: python scripts/build-appstore-icons.py --refresh-app-store");
  process.exit(1);
}
const p=spawnSync("python3",["scripts/build-appstore-icons.py","--refresh-app-store"],{stdio:"inherit"});
if(p.error) throw p.error;
process.exit(p.status??1);
