// @ts-nocheck
import zxcvbn from "zxcvbn";
export default zxcvbn;
if (typeof window !== 'undefined') {
    window.zxcvbn = zxcvbn;
}
