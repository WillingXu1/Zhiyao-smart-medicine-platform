import { r as registerInstance, h, H as Host } from './index-ab3c86da.js';
import { n as notSupport } from './helper-8a85bb65.js';
import '@tarojs/taro';

const NestedScrollBody = class {
  constructor(hostRef) {
    registerInstance(this, hostRef);
  }
  componentDidLoad() {
    notSupport('NestedScrollBody', this);
  }
  render() {
    return (h(Host, null));
  }
};

export { NestedScrollBody as taro_nested_scroll_body_core };
