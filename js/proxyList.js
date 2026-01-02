// proxyList.js - 代理列表管理模块

// 代理配置
const proxyList = window.proxyList = [
    {name: 'GHProxy', url: 'https://ghproxy.com/'},
    {name: 'ghp-ci', url: 'https://ghp.ci/'},
    {name: 'halonice', url: 'http://gh.halonice.com/'},
    {name: 'gitdl-cn', url: 'https://gitdl.cn/'},
    {name: 'gh.xxooo', url: 'https://gh.xxooo.cf/'},
    {name: 'kr2-proxy', url: 'http://kr2-proxy.gitwarp.com:9980'},
    {name: 'moeyy', url: 'https://github.moeyy.xyz/'},
    {name: 'jp-proxy', url: 'http://jp-proxy.gitwarp.com:3000/'},
    {name: 'gh-proxy-org', url: 'https://gh-proxy.org/'},
    {name: 'ghproxyNet', url: 'https://ghproxy.net/'},
    {name: 'bgithub', url: 'https://raw.bgithub.xyz/'},
    {name: '直接访问', url: ''}
];

// 测速目标文件 - 使用小文件提高测速速度
const testFile = 'https://github.com/zitengjushi/zitengjushi.github.io/blob/main/README.md';

// 测速函数
export async function testProxySpeed(proxy) {
    const startTime = performance.now();
    try {
        // 构建请求URL：如果代理URL为空则直接访问testFile
        const requestUrl = proxy.url ? proxy.url + testFile : testFile;
        
        // 使用HEAD请求减少数据传输，添加禁用缓存和减少请求头选项
        const response = await fetch(requestUrl, {
            method: 'HEAD',
            mode: 'cors',
            timeout: 2000, // 2秒超时，平衡速度和准确性
            cache: 'no-cache', // 禁用缓存，确保每次测试都是新请求
            headers: {
                'Accept': '*/*', // 接受所有类型的响应
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        });
        
        if (!response.ok) {
            return { proxy, speed: -1, error: `HTTP错误: ${response.status}` };
        }
        
        const endTime = performance.now();
        const speed = Math.round(endTime - startTime); // 毫秒
        return { proxy, speed, error: null };
    } catch (error) {
        return { proxy, speed: -1, error: error.message };
    }
}

// 批量测速 - 并行测试所有代理，提高速度
export async function testAllProxies(selector = null, onProxySelectedCallback = null) {
    const results = [];
    
    // 创建一个Promise数组，并行测试所有代理
    const testPromises = proxyList.map(async (proxy) => {
        try {
            const result = await testProxySpeed(proxy);
            
            // 更新proxyList，添加测速结果
            proxy.speed = result.speed;
            proxy.error = result.error;
            
            // 如果提供了选择器，立即更新显示
            if (selector) {
                updateProxySelectorWithSpeed(selector);
            }
            
            return result;
        } catch (error) {
            console.error(`测试代理${proxy.name}时出错:`, error);
            proxy.speed = -1;
            proxy.error = error.message;
            
            // 如果提供了选择器，立即更新显示
            if (selector) {
                updateProxySelectorWithSpeed(selector);
            }
            
            return { proxy, speed: -1, error: error.message };
        }
    });
    
    // 等待所有测试完成
    results.push(...await Promise.all(testPromises));
    
    // 测试完成后，自动选择第一个测试成功的代理
    if (selector) {
        const firstSuccessProxy = proxyList.find(proxy => proxy.speed > 0);
        if (firstSuccessProxy) {
            // 更新选择器的选中状态
            selector.value = firstSuccessProxy.url;
            // 保存到localStorage
            saveSelectedProxy(firstSuccessProxy.url);
            
            // 如果提供了回调函数，调用它以应用新的代理规则
            if (onProxySelectedCallback && typeof onProxySelectedCallback === 'function') {
                onProxySelectedCallback(firstSuccessProxy.url);
            }
        }
    }
    
    return results;
}

// 更新代理选择器，显示测速结果
export function updateProxySelectorWithSpeed(selector) {
    proxyList.forEach(proxy => {
        const option = Array.from(selector.options).find(opt => opt.value === proxy.url);
        if (option) {
            if (proxy.speed > 0) {
                option.textContent = `${proxy.name} (${proxy.speed}ms)`;
            } else if (proxy.error) {
                option.textContent = `${proxy.name} (访问失败)`;
            }
        }
    });
}

// 填充代理选择器
export function populateProxySelector(selector) {
    // 清空现有选项
    selector.innerHTML = '';
    
    // 添加代理选项
    proxyList.forEach(proxy => {
        const option = document.createElement('option');
        option.value = proxy.url;
        option.textContent = proxy.name;
        selector.appendChild(option);
    });
}

// 获取当前选中的代理
export function getSelectedProxy() {
    return localStorage.getItem('selectedProxy') || '';
}

// 保存选中的代理
export function saveSelectedProxy(proxyUrl) {
    localStorage.setItem('selectedProxy', proxyUrl);
}

// 初始化代理选择器
export function initProxySelector(selectorId) {
    const selector = document.getElementById(selectorId);
    if (!selector) return;
    
    // 填充代理选择器
    populateProxySelector(selector);
    
    // 初始化选中状态
    selector.value = getSelectedProxy();
    
    // 监听选择变化
    selector.addEventListener('change', (e) => {
        saveSelectedProxy(e.target.value);
        window.location.reload();
    });
    
    return selector;
}

// 处理代理URL
export function getProxiedUrl(url, proxy) {
    if (!proxy) proxy = getSelectedProxy();
    
    let proxiedUrl;
    
    // 处理代理逻辑
    if (proxy === 'https://raw.bgithub.xyz/') {
        // 特殊情况：如果选择的代理是 https://raw.bgithub.xyz/
        if (url.includes('https://raw.githubusercontent.com/')) {
            // 把 https://raw.githubusercontent.com 前面的地址去掉，并替换为 https://raw.bgithub.xyz
            proxiedUrl = url.replace(/^(.*?)(https:\/\/raw\.githubusercontent\.com\/)/, 'https://raw.bgithub.xyz/');
        } else if (url.includes('https://github.com/')) {
            // 处理 https://github.com/ 开头的地址
            proxiedUrl = url.replace(/^(.*?)(https:\/\/github\.com\/)/, 'https://raw.bgithub.xyz/');
        } else {
            // 其他情况保持不变
            proxiedUrl = url;
        }
    } else if (url.startsWith('https://raw.githubusercontent.com/') || url.startsWith('https://github.com/')) {
        // 1. 如果网址以 https://raw.githubusercontent.com 或 https://github.com 开头前面没有其他地址
        proxiedUrl = proxy ? `${proxy}${url}` : url;
    } else if (url.includes('https://raw.githubusercontent.com/') || url.includes('https://github.com/')) {
        // 2. 如果网址 https://raw.githubusercontent.com 或 https://github.com 前面有其他地址
        proxiedUrl = proxy ? `${proxy}${url.replace(/^(.*?)(https:\/\/(raw\.)?github(usercontent)?\.com\/)/, '$2')}` : url.replace(/^(.*?)(https:\/\/(raw\.)?github(usercontent)?\.com\/)/, '$2');
    } else if (url.startsWith('https://raw.bgithub.xyz/')) {
        // 3. 如果地址以 https://raw.bgithub.xyz 开头
        const rawGithubUrl = url.replace('https://raw.bgithub.xyz/', 'https://raw.githubusercontent.com/');
        proxiedUrl = proxy ? `${proxy}${rawGithubUrl}` : rawGithubUrl;
    } else {
        // 其他情况保持不变
        proxiedUrl = url;
    }
    
    return proxiedUrl;
}