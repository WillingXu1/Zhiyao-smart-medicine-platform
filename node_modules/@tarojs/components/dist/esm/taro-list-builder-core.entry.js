import { r as registerInstance, h, H as Host } from './index-ab3c86da.js';
import { n as notSupport } from './helper-8a85bb65.js';
import '@tarojs/taro';

const ListBuilder = class {
  constructor(hostRef) {
    registerInstance(this, hostRef);
  }
  componentDidLoad() {
    notSupport('ListBuilder', this);
  }
  render() {
    return (h(Host, null));
  }
};

export { ListBuilder as taro_list_builder_core };
