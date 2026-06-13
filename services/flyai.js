/**
 * 飞猪旅行搜索服务 - 模拟 flyai skill 核心功能
 * 提供景点预订搜索和跳转能力
 * 
 * 功能：
 * 1. 根据景点名称生成飞猪搜索链接
 * 2. 批量添加预订链接到目的地列表
 * 3. 支持多种旅行产品类型（酒店、门票、跟团游）
 */

class FlyaiService {
  static FLIGGY_SEARCH_URL = 'https://travel.fliggy.com/search';
  static FLIGGY_DEST_URL = 'https://travel.fliggy.com/dest';
  
  /**
   * 根据景点名称生成飞猪搜索URL
   * @param {string} destinationName - 景点名称
   * @param {string} productType - 产品类型: 'all', 'hotel', 'ticket', 'tour'
   * @returns {string} 飞猪搜索链接
   */
  static getSearchUrl(destinationName, productType = 'all') {
    let query = destinationName;
    switch(productType) {
      case 'hotel':
        query = `${destinationName} 酒店`;
        break;
      case 'ticket':
        query = `${destinationName} 门票`;
        break;
      case 'tour':
        query = `${destinationName} 跟团游`;
        break;
      default:
        query = `${destinationName} 旅行`;
    }
    
    return `${this.FLIGGY_SEARCH_URL}?q=${encodeURIComponent(query)}`;
  }
  
  /**
   * 获取预订跳转链接（带跟踪参数）
   * @param {string} destinationName 
   * @param {number|string} destinationId 
   * @param {string} productType
   * @returns {string}
   */
  static getBookingUrl(destinationName, destinationId, productType = 'all') {
    const baseUrl = this.getSearchUrl(destinationName, productType);
    // 添加来源跟踪，便于分析转化
    const separator = baseUrl.includes('?') ? '&' : '?';
    return `${baseUrl}${separator}utm_source=100trips&utm_medium=web&utm_campaign=booking&dest_id=${destinationId}`;
  }
  
  /**
   * 批量生成多个目的地的预订链接
   * @param {Array} destinations - 目的地数组，每个元素需包含 id 和 name
   * @returns {Array} 添加了 bookingUrl 字段的目的地数组
   */
  static enrichDestinationsWithBookingUrl(destinations) {
    if (!Array.isArray(destinations)) {
      return [];
    }
    
    return destinations.map(dest => ({
      ...dest,
      bookingUrl: this.getBookingUrl(dest.name, dest.id),
      // 同时提供分类型的预订链接
      bookingUrls: {
        all: this.getBookingUrl(dest.name, dest.id, 'all'),
        hotel: this.getBookingUrl(dest.name, dest.id, 'hotel'),
        ticket: this.getBookingUrl(dest.name, dest.id, 'ticket'),
        tour: this.getBookingUrl(dest.name, dest.id, 'tour')
      }
    }));
  }
  
  /**
   * 生成带参数的跳转HTML（用于前端嵌入）
   * @param {string} destinationName 
   * @param {number|string} destinationId
   * @returns {string} HTML按钮代码
   */
  static generateBookingButton(destinationName, destinationId) {
    const url = this.getBookingUrl(destinationName, destinationId);
    return `<a href="${url}" target="_blank" rel="noopener noreferrer" 
              class="inline-block bg-orange-500 hover:bg-orange-600 text-white font-bold py-2 px-4 rounded-lg transition duration-300">
              🎫 在飞猪查看预订
            </a>`;
  }
  
  /**
   * 搜索建议（模拟飞猪的搜索建议）
   * @param {string} keyword 
   * @returns {Array} 搜索建议列表
   */
  static getSearchSuggestions(keyword) {
    // 这里可以对接真实的搜索建议API
    const suggestions = [
      `${keyword} 自由行`,
      `${keyword} 当地玩乐`,
      `${keyword} 特色体验`,
      `${keyword} 定制游`
    ];
    return suggestions.map(s => ({
      keyword: s,
      url: this.getSearchUrl(s)
    }));
  }
}

module.exports = FlyaiService;

// 如果直接运行此文件，测试功能
if (require.main === module) {
  console.log('=== 飞猪服务测试 ===\n');
  
  // 测试生成搜索链接
  const testDestination = '冰岛';
  console.log(`1. 搜索链接: ${FlyaiService.getSearchUrl(testDestination)}`);
  console.log(`2. 酒店链接: ${FlyaiService.getSearchUrl(testDestination, 'hotel')}`);
  console.log(`3. 门票链接: ${FlyaiService.getSearchUrl(testDestination, 'ticket')}`);
  
  // 测试批量添加
  const testDestinations = [
    { id: 1, name: '冰岛' },
    { id: 2, name: '挪威' }
  ];
  console.log('\n4. 批量添加预订链接:');
  const enriched = FlyaiService.enrichDestinationsWithBookingUrl(testDestinations);
  console.log(JSON.stringify(enriched, null, 2));
  
  // 测试生成按钮
  console.log('\n5. 生成的按钮HTML:');
  console.log(FlyaiService.generateBookingButton('冰岛', 1));
}
