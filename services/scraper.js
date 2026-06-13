/**
 * 网页内容采集系统 — Wikipedia & National Geographic 搜索
 *
 * 使用方式:
 *   node services/scraper.js wikipedia "Tromso Norway"
 *   node services/scraper.js natgeo "Amazon Rainforest"
 */

const BASE_WIKI = 'https://en.wikipedia.org/w/api.php';
const BASE_NATGEO = 'https://www.nationalgeographic.com/search';

/**
 * 搜索 Wikipedia 并返回页面 URL 和摘要
 */
async function searchWikipedia(query) {
  const params = new URLSearchParams({
    action: 'query',
    format: 'json',
    list: 'search',
    srsearch: query,
    srlimit: 3,
    origin: '*',
  });

  try {
    const res = await fetch(`${BASE_WIKI}?${params}`);
    const data = await res.json();

    if (!data.query || !data.query.search.length) {
      return { success: false, results: [], message: 'No Wikipedia results found' };
    }

    const results = data.query.search.map((item) => ({
      title: item.title,
      pageId: item.pageid,
      snippet: item.snippet.replace(/<\/?[^>]+(>|$)/g, ''), // strip HTML
      url: `https://en.wikipedia.org/wiki/${encodeURIComponent(item.title.replace(/ /g, '_'))}`,
      wordCount: item.wordcount,
      timestamp: item.timestamp,
    }));

    return { success: true, results };
  } catch (err) {
    return { success: false, results: [], message: err.message };
  }
}

/**
 * 获取 Wikipedia 页面全文摘要（extract）
 */
async function getWikipediaExtract(pageTitle) {
  const params = new URLSearchParams({
    action: 'query',
    format: 'json',
    prop: 'extracts|info',
    exintro: '1',
    explaintext: '1',
    inprop: 'url',
    titles: pageTitle,
    origin: '*',
  });

  try {
    const res = await fetch(`${BASE_WIKI}?${params}`);
    const data = await res.json();
    const pages = data.query.pages;
    const page = Object.values(pages)[0];

    if (!page || page.missing) {
      return { success: false, message: 'Page not found' };
    }

    return {
      success: true,
      title: page.title,
      extract: page.extract,
      url: page.fullurl || `https://en.wikipedia.org/wiki/${encodeURIComponent(pageTitle.replace(/ /g, '_'))}`,
    };
  } catch (err) {
    return { success: false, message: err.message };
  }
}

/**
 * 返回 National Geographic 搜索 URL
 */
function searchNationalGeographic(query) {
  const encoded = encodeURIComponent(query);
  return {
    success: true,
    label: 'National Geographic',
    searchUrl: `${BASE_NATGEO}?q=${encoded}`,
    results: [
      {
        title: `National Geographic Search: ${query}`,
        url: `${BASE_NATGEO}?q=${encoded}`,
        snippet: `Search National Geographic for articles, photos, and documentaries about "${query}".`,
      },
    ],
  };
}

/**
 * 综合搜索：同时查询 Wikipedia + 生成 NatGeo 链接
 */
async function searchAll(query) {
  const [wiki, natgeo] = await Promise.all([
    searchWikipedia(query),
    Promise.resolve(searchNationalGeographic(query)),
  ]);

  return {
    query,
    sources: {
      wikipedia: wiki,
      nationalGeographic: natgeo,
    },
  };
}

// ── CLI ────────────────────────────────────────────────────────────────────
if (require.main === module) {
  const [,, source, ...queryParts] = process.argv;
  const query = queryParts.join(' ');

  if (!query) {
    console.log('Usage: node scraper.js <wikipedia|natgeo|all> "<search query>"');
    process.exit(1);
  }

  (async () => {
    switch (source) {
      case 'wikipedia': {
        const result = await searchWikipedia(query);
        console.log(JSON.stringify(result, null, 2));
        break;
      }
      case 'natgeo': {
        const result = searchNationalGeographic(query);
        console.log(JSON.stringify(result, null, 2));
        break;
      }
      case 'all': {
        const result = await searchAll(query);
        console.log(JSON.stringify(result, null, 2));
        break;
      }
      default:
        console.log(`Unknown source: ${source}. Use: wikipedia | natgeo | all`);
    }
  })();
}

// ── 导出 ────────────────────────────────────────────────────────────────────
module.exports = {
  searchWikipedia,
  getWikipediaExtract,
  searchNationalGeographic,
  searchAll,
};
