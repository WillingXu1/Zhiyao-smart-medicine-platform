declare function makeMap(str: string, expectsLowerCase?: boolean): (key: string) => boolean;
declare const specialMiniElements: {
    img: string;
    iframe: string;
};
interface SpecialMap {
    mapName: (props: Record<string, string | boolean>) => string;
}
declare const getSpecialElementMapping: (tag: string, expectsLowerCase?: boolean) => SpecialMap | undefined;
declare const isMiniElements: (key: string) => boolean;
declare const isInlineElements: (key: string) => boolean;
declare const isBlockElements: (key: string) => boolean;
declare const isSpecialElements: (key: string) => boolean;
export { makeMap, specialMiniElements, getSpecialElementMapping, isMiniElements, isInlineElements, isBlockElements, isSpecialElements };
