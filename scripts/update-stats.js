const fs = require('fs');
const path = require('path');

const YOUTUBE_API_KEY = process.env.YOUTUBE_API_KEY;

// Creator mappings
const creators = {
  faceme: { yt: '@FaceMeGaming', ig: 'ig_faceme' },
  kaur:   { yt: '@kauroplive', ig: 'kauroplivee' },
  samar:  { yt: '@SamarPlayz', ig: 'ig_samarplayz' },
  fizzer: { yt: '@OnlyFizZer', ig: 'only_fizzer' },
  amy:    { yt: '@MissAmyGaming', ig: 'missamygaming' },
  tabby:  { yt: '@TabbyBgmi', ig: 'tabbybgmi' }
};

// Utilities to format numbers
function formatNumber(numStr) {
  const num = parseInt(numStr, 10);
  if (isNaN(num)) return numStr;
  if (num >= 1000000) return (num / 1000000).toFixed(1).replace(/\.0$/, '') + 'M';
  if (num >= 1000) return (num / 1000).toFixed(1).replace(/\.0$/, '') + 'K';
  return num.toString();
}

async function fetchYoutubeSubs(handle) {
  if (!YOUTUBE_API_KEY) {
    console.warn('YOUTUBE_API_KEY not found. Skipping YouTube fetch for', handle);
    return null;
  }
  try {
    const url = `https://youtube.googleapis.com/youtube/v3/channels?part=statistics&forHandle=${handle}&key=${YOUTUBE_API_KEY}`;
    const response = await fetch(url);
    if (!response.ok) throw new Error(`YouTube API returned ${response.status}`);
    const data = await response.json();
    if (data.items && data.items.length > 0) {
      return formatNumber(data.items[0].statistics.subscriberCount);
    }
  } catch (err) {
    console.error('Error fetching YouTube for', handle, err.message);
  }
  return null;
}

async function fetchInstagramFollowers(handle) {
  try {
    // Attempting a public scrape of the Instagram profile
    const url = `https://www.instagram.com/${handle}/`;
    const response = await fetch(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
      }
    });

    if (!response.ok) throw new Error(`Instagram returned ${response.status}`);
    const html = await response.text();

    // Look for the meta description tag which usually contains: "XXX Followers, YYY Following, ZZZ Posts..."
    const metaMatch = html.match(/<meta\s+name="description"\s+content="([^"]+)"/i);
    if (metaMatch && metaMatch[1]) {
      const desc = metaMatch[1];
      const match = desc.match(/([\d\.,]+[KMB]?)\s+Followers/i);
      if (match && match[1]) {
        let countStr = match[1].replace(/,/g, '');
        // Sometimes it says "1.2M", "575K", or "1243"
        if (countStr.includes('K') || countStr.includes('M')) {
          return countStr;
        } else {
          return formatNumber(countStr);
        }
      }
    }
  } catch (err) {
    console.error('Error fetching Instagram for', handle, err.message);
  }
  return null;
}

async function main() {
  const statsPath = path.join(__dirname, '../js/data/stats.json');
  let currentStats = {};
  
  if (fs.existsSync(statsPath)) {
    currentStats = JSON.parse(fs.readFileSync(statsPath, 'utf8'));
  }

  for (const [key, handles] of Object.entries(creators)) {
    console.log(`Processing ${key}...`);
    
    const ytSubs = await fetchYoutubeSubs(handles.yt);
    const igFollowers = await fetchInstagramFollowers(handles.ig);

    // Initialize if empty
    if (!currentStats[key]) currentStats[key] = {};

    // Only update if we successfully fetched the new data to prevent overriding with nulls on failure
    if (ytSubs) {
      currentStats[key].youtube_subs = ytSubs;
      console.log(`  YouTube: ${ytSubs}`);
    } else {
      console.log(`  YouTube: [Failed] Keeping old: ${currentStats[key].youtube_subs || 'None'}`);
    }

    if (igFollowers) {
      currentStats[key].instagram_followers = igFollowers;
      console.log(`  Instagram: ${igFollowers}`);
    } else {
      console.log(`  Instagram: [Failed] Keeping old: ${currentStats[key].instagram_followers || 'None'}`);
    }
  }

  fs.writeFileSync(statsPath, JSON.stringify(currentStats, null, 2), 'utf8');
  console.log('Successfully updated stats.json');
}

main().catch(err => {
  console.error("Fatal Error:", err);
  process.exit(1);
});
