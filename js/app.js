document.addEventListener('DOMContentLoaded', function() {
  // 加载IPTV数据
  fetch('./iptv.json')
    .then(response => {
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      return response.json();
    })
    .then(data => {
      console.log('IPTV数据加载成功:', data);
      const container = document.getElementById('iptvContainer');
      data.forEach(provinceData => {
        const div = document.createElement('div');
        div.className = 'province-row';
        div.innerHTML = `
          <span class="province-name">${provinceData.province}</span>
          <div class="operator-links" style="display: flex; gap: 30px;">
            ${['unicom', 'mobile', 'telecom'].map(operator => {
              const u = provinceData[operator].unicast;
              const m = provinceData[operator].multicast;
              const uninamem = provinceData[operator].uniname;
              const multiname = provinceData[operator].multiname;
              return `
                <div class="operator-group">
                  <a href="${u}" class="unicast-link" data-url="${u}">
                    ${uninamem}
                  </a>
                    <a href="${u}" class="multicast-link" data-url="${m}">
                      ${multiname}
                    </a>
                </div>`;
            }).join('')}
          </div>
          <div class="update-time">${provinceData.update_date}</div>
        `;
        container.appendChild(div);
      });
    })
    .catch(error => {
      console.error('加载IPTV数据失败:', error);
      document.getElementById('iptvContainer').innerHTML = `❌ 数据加载失败: ${error.message}`;
    });
  // 代理配置
  const proxyList = window.proxyList = [
    {name: 'GHProxy', url: 'https://ghproxy.com/'},
    {name: 'GitMirror', url: 'https://mirror.ghproxy.com/'},
    {name: 'moeyy', url: 'https://github.moeyy.xyz/'},
    {name: 'gh-proxy', url: 'https://gh-proxy.com/'},
    {name: 'ghproxyNet', url: 'https://ghproxy.net/'},
    {name: 'bgithub', url: 'https://raw.bgithub.xyz/'},
    {name: '直接访问', url: ''}
  ];
  

  // 创建代理选择器
  const proxySelector = document.createElement('select');
  proxySelector.id = 'proxySelect';
  proxySelector.className = 'proxy-select';
  
  (window.proxyList || []).forEach(proxy => {
    const option = document.createElement('option');
    option.value = proxy.url;
    option.textContent = proxy.name;
    proxySelector.appendChild(option);
  });

  document.querySelector('.main-container').prepend(proxySelector);

  // 初始化选中状态
  proxySelector.value = getSelectedProxy();
  // 显示当前代理名称
  document.querySelector('#proxyStatus').textContent = `当前代理: ${proxyList.find(p => p.url === proxySelector.value)?.url || '无'}`;

  // 获取当前代理
  function getSelectedProxy() {
    return localStorage.getItem('selectedProxy') || '';
  }

  // IPTV链接点击处理
  document.getElementById('iptvContainer').addEventListener('click', function(e) {
    if (e.target.classList.contains('source-link')) {
      e.preventDefault();
      const originalUrl = e.target.dataset.url;
      let processedUrl = originalUrl;
      
      if (originalUrl.includes('raw.githubusercontent.com')) {
        processedUrl = `${getSelectedProxy()}${originalUrl}`;
      } else if (getSelectedProxy()) {
        processedUrl = originalUrl.replace(/^.*?raw\.githubusercontent\.com\//, `${getSelectedProxy()}raw.githubusercontent.com/`);
      }
      
      navigator.clipboard.writeText(processedUrl);
      showToast('直播源地址已复制');
    }
  });

  // 监听选择变化
  proxySelector.addEventListener('change', (e) => {
    localStorage.setItem('selectedProxy', e.target.value);
    window.location.reload();
  });

    // 动态加载函数
    async function loadData(url, container) {
        try {
            const proxy = getSelectedProxy() || '';
    const baseUrl = url.includes('https://raw.githubusercontent.com/') 
  ? url.replace(/^(.*?)(https:\/\/raw\.githubusercontent\.com\/)/, '$2') 
  : url;
    const proxiedUrl = url.includes('https://raw.githubusercontent.com/') 
    ? `${proxy}${baseUrl}`
    : url;
    console.log('Using proxy:', getSelectedProxy());
    const response = await fetch(proxiedUrl);
            const data = await response.json();
            data.urls.forEach(item => {
                const div = document.createElement('div');
                div.className = 'link-item';
                const link = document.createElement('a');
                const processedUrl = item.url.includes('https://raw.githubusercontent.com/') 
  ? `${getSelectedProxy()}${item.url.replace(/^(.*?)(https:\/\/raw\.githubusercontent\.com\/)/, '$2')}` 
  : item.url;
        link.href = processedUrl;
                link.innerHTML = `${item.name} 
                    <div class="copy-group">
                        <button class="copy-btn" data-url="${item.url}">
                            <svg viewBox="0 0 24 24">
                                <path d="M19 21H8V7h11m0-2H8a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h11a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2m-3-4H4a2 2 0 0 0-2 2v14h2V3h12V1z"/>
                            </svg>
                        </button>
                        <span class="copy-label">单线</span>
                    </div>`;
                link.target = '_blank';
                div.appendChild(link);
                container.appendChild(div);
            });
        } catch (error) {
            console.error('加载失败:', error);
        }
    }

    // 初始化加载duocang.json
    fetch('./duocang.json')
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById('linkContainer');
            data.urls.forEach(item => {
                const div = document.createElement('div');
                div.className = 'link-item';
                const link = document.createElement('a');
                const processedUrl = item.url.includes('https://raw.githubusercontent.com/') 
  ? `${getSelectedProxy()}${item.url.replace(/^(.*?)(https:\/\/raw\.githubusercontent\.com\/)/, '$2')}` 
  : item.url;
        link.href = processedUrl;
                link.innerHTML = `${item.name} 
                    <div class="copy-group">
                        <button class="copy-btn" data-url="${item.url}">
                            <svg viewBox="0 0 24 24">
                                <path d="M19 21H8V7h11m0-2H8a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h11a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2m-3-4H4a2 2 0 0 0-2 2v14h2V3h12V1z"/>
                            </svg>
                        </button>
                        <span class="copy-label">单线</span>
                    </div>`;
                link.target = '_blank';
                div.appendChild(link);
                container.appendChild(div);
            });
        })
        .catch(error => console.error('加载数据失败:', error));
    
    // 复制功能实现
    // 统一提示元素
    const toast = document.createElement('div');
    toast.className = 'toast';
    document.body.appendChild(toast);

    // 重构复制处理函数
    async function handleCopy(url) {
    const baseUrl = url.includes('https://raw.githubusercontent.com/') 
  ? url.replace(/^(.*?)(https:\/\/raw\.githubusercontent\.com\/)/, '$2') 
  : url;
    const fullUrl = url.includes('https://raw.githubusercontent.com/') 
    ? `${getSelectedProxy()}${baseUrl}`
    : url
        try {
            if(navigator.clipboard) {
                await navigator.clipboard.writeText(fullUrl);
            } else {
                // 兼容旧版浏览器
                const textarea = document.createElement('textarea');
                textarea.value = fullUrl;
                document.body.appendChild(textarea);
                textarea.select();
                document.execCommand('copy');
                document.body.removeChild(textarea);
            }
            toast.textContent = `✅ 已复制：${fullUrl}`;
            toast.style.display = 'block';
            setTimeout(() => toast.style.display = 'none', 2000);
        } catch (err) {
            toast.textContent = '❌ 复制失败，请手动复制';
            toast.style.display = 'block';
            setTimeout(() => toast.style.display = 'none', 3000);
            console.error('复制失败:', err);
        }
    }

    // 仓库折叠功能
    const repoToggle = document.querySelector('#repoToggle');
    const repoSection = document.querySelector('.repo-section');
    
    // 原资源列表折叠功能
    const toggleBtn = document.querySelector('.toggle-btn:not(#repoToggle)');
    const linkList = document.getElementById('linkContainer');
    
    // 加载duocang.json生成二级标题
    fetch('./duocang.json')
        .then(res => res.json())
        .then(data => {
            const subSections = document.getElementById('subSections');
            data.storeHouse.forEach(item => {
                const proxiedSourceUrl = item.sourceUrl.includes('https://raw.githubusercontent.com/')  ? `${getSelectedProxy()}${item.sourceUrl.replace(/^(.*?)(https:\/\/raw\.githubusercontent\.com\/)/, '$2')}` 
  : item.sourceUrl;
        const section = createSubSection(item.sourceName, proxiedSourceUrl);
                section.querySelector('.toggle-btn').classList.add('collapsed');
                section.querySelector('.link-list').classList.add('collapsed');
                subSections.appendChild(section);
            });
        });

    // 初始状态设为双折叠
    repoSection.classList.add('collapsed');
    repoToggle.classList.add('collapsed');
    linkList.classList.add('collapsed');
    toggleBtn.classList.add('collapsed');
    
    // 仓库标题点击事件
    // 生成二级标题函数
    function createSubSection(sourceName, sourceUrl) {
        const section = document.createElement('div');
        section.className = 'sub-section collapsed';
        section.innerHTML = `
            <div class="section-header">
                <div style="display: flex; align-items: center; width: 100%;">
                    <button class="toggle-btn" data-url="${sourceUrl}" style="flex-grow: 1;">
                        <svg class="arrow-icon" viewBox="0 0 24 24">
                            <path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z"/>
                        </svg>
                        ${sourceName}
                    </button>
                    <button class="copy-btn" data-url="${sourceUrl}">
                        <svg viewBox="0 0 24 24" width="18" height="18">
                            <path d="M19 21H8V7h11m0-2H8a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h11a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2m-3-4H4a2 2 0 0 0-2 2v14h2V3h12V1z"/>
                        </svg>
                    </button>
                    <span class="copy-label">多线</span>
                </button>
            </div>
            <div class="link-list"></div>
        `;
        return section;
    }

    // 处理仓库标题点击
    repoToggle.addEventListener('click', () => {
        repoSection.classList.toggle('collapsed');
        repoToggle.classList.toggle('collapsed');
    });

    // 资源列表标题点击事件
    toggleBtn.addEventListener('click', () => {
        linkList.classList.toggle('collapsed');
        toggleBtn.classList.toggle('collapsed');
    });

    // 二级标题点击事件
    document.addEventListener('click', (e) => {
        const btn = e.target.closest('.toggle-btn');
        if(btn && btn.dataset.url) {
            const list = btn.parentElement.nextElementSibling;
            list.innerHTML = ''; // 清空旧内容
            btn.classList.toggle('collapsed');
            list.classList.toggle('collapsed');
            
            if (!list.classList.contains('collapsed')) {
                loadData(btn.dataset.url, list);
            }
        }
    });

    // 事件委托优化
    document.addEventListener('click', (e) => {
        const btn = e.target.closest('.copy-btn');
        if(btn) {
            e.preventDefault();
            e.stopImmediatePropagation();
            handleCopy(btn.dataset.url);
        }
    });
});