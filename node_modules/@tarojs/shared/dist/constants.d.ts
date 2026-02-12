declare enum PLATFORM_TYPE {
    MINI = "mini",
    WEB = "web",
    RN = "rn",
    HARMONY = "harmony",
    QUICK = "quickapp",
    ASCF = "ascf"
}
declare const PLATFORM_CONFIG_MAP: {
    h5: {
        type: PLATFORM_TYPE;
    };
    harmony: {
        type: PLATFORM_TYPE;
    };
    mini: {
        type: PLATFORM_TYPE;
    };
    rn: {
        type: PLATFORM_TYPE;
    };
    quickapp: {
        type: PLATFORM_TYPE;
    };
    ascf: {
        type: PLATFORM_TYPE;
    };
};
export { PLATFORM_TYPE, PLATFORM_CONFIG_MAP };
