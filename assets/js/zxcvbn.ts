
import zxcvbn from "zxcvbn";
export default zxcvbn;
if (typeof window !== 'undefined') { (window as any).zxcvbn = zxcvbn; }
