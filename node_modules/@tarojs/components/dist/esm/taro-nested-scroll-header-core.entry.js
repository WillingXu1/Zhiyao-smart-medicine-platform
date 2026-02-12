import { r as registerInstance, h, H as Host } from './index-ab3c86da.js';
import { n as notSupport } from './helper-8a85bb65.js';
import '@tarojs/taro';

const NestedScrollHeader = class {
  constructor(hostRef) {
    registerInstance(this, hostRef);
  }
  componentDidLoad() {
    notSupport('NestedScrollHeader', this);
  }
  render() {
    return (h(Host, null));
  }
};

export { NestedScrollHeader as taro_nested_scroll_header_core };
