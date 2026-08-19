// proxyList.js - 代理列表管理模块

// 代理配置
const proxyList = window.proxyList = [
    {name: 'gh-proxy-org', url: 'https://gh-proxy.org/'},
    {name: 'ghproxyNet', url: 'https://ghproxy.net/'},
    {name: 'b.yesican.top', url: 'https://b.yesican.top/'},
    {name: 'd.6519.top', url: 'https://d.6519.top/'},
    {name: 'd.scyun.top', url: 'https://d.scyun.top/'},
    {name: 'bgithub', url: 'https://raw.bgithub.xyz/'},
    {name: 'gh-proxy.com', url: 'https://gh-proxy.com/'},
    {name: 'github.tbap.top', url: 'https://github.tbap.top/'},
    {name: 'github.dpik.top', url: 'https://github.dpik.top/'},
    {name: 'gh.dpik.top', url: 'https://gh.dpik.top/'},
    {name: 'ghf.无名氏.top', url: 'https://ghf.无名氏.top/'},
    {name: 'github-proxy.memory-echoes.cn', url: 'https://github-proxy.memory-echoes.cn/'},
    {name: 'ghfile.geekertao.top', url: 'https://ghfile.geekertao.top/'},
    {name: 'git.yylx.win', url: 'https://git.yylx.win/'},
    {name: 'cdn.gh-proxy.com', url: 'https://cdn.gh-proxy.com/'},
    {name: 'jiashu.1win.eu.org', url: 'https://jiashu.1win.eu.org/'},
    {name: 'gh.bugdey.us.kg', url: 'https://gh.bugdey.us.kg/'},
    {name: 'gh.927223.xyz', url: 'https://gh.927223.xyz/'},
    {name: 'down.mxw.xx.kg', url: 'https://down.mxw.xx.kg/'},
    {name: '777.z321.cc.cd', url: 'https://777.z321.cc.cd/'},
    {name: 'cdn.akaere.online', url: 'https://cdn.akaere.online/'},
    {name: 'cfgh.ikgy.top', url: 'https://cfgh.ikgy.top/'},
    {name: 'down.mxw.qzz.io', url: 'https://down.mxw.qzz.io/'},
    {name: 'fastgit.cc', url: 'https://fastgit.cc/'},
    {name: 'free.cn.eu.org', url: 'https://free.cn.eu.org/'},
    {name: 'g.blfrp.cn', url: 'https://g.blfrp.cn/'},
    {name: 'g.z321.cc.cd', url: 'https://g.z321.cc.cd/'},
    {name: 'gap.andyjin.website', url: 'https://gap.andyjin.website/'},
    {name: 'gg.z321.cc.cd', url: 'https://gg.z321.cc.cd/'},
    {name: 'gh.07150721.xyz', url: 'https://gh.07150721.xyz/'},
    {name: 'gh.acmsz.top', url: 'https://gh.acmsz.top/'},
    {name: 'gh.b52m.cn', url: 'https://gh.b52m.cn/'},
    {name: 'gh.catmak.name', url: 'https://gh.catmak.name/'},
    {name: 'gh.chjina.com', url: 'https://gh.chjina.com/'},
    {name: 'gh.ddlc.top', url: 'https://gh.ddlc.top/'},
    {name: 'gh.felicity.ac.cn', url: 'https://gh.felicity.ac.cn/'},
    {name: 'gh.idayer.com', url: 'https://gh.idayer.com/'},
    {name: 'gh.jasonzeng.dev', url: 'https://gh.jasonzeng.dev/'},
    {name: 'gh.jjj.gv.uy', url: 'https://gh.jjj.gv.uy/'},
    {name: 'gh.meali.top', url: 'https://gh.meali.top/'},
    {name: 'gh.monlor.com', url: 'https://gh.monlor.com/'},
    {name: 'gh.my-website.ccwu.cc', url: 'https://gh.my-website.ccwu.cc/'},
    {name: 'gh.noki.icu', url: 'https://gh.noki.icu/'},
    {name: 'gh.qfmc0721.cc.cd', url: 'https://gh.qfmc0721.cc.cd/'},
    {name: 'gh.ruan.dpdns.org', url: 'https://gh.ruan.dpdns.org/'},
    {name: 'gh.sixyin.com', url: 'https://gh.sixyin.com/'},
    {name: 'gh.tryxd.cn', url: 'https://gh.tryxd.cn/'},
    {name: 'gh.zhai.edu.pl', url: 'https://gh.zhai.edu.pl/'},
    {name: 'ghfast.top', url: 'https://ghfast.top/'},
    {name: 'ghm.078465.xyz', url: 'https://ghm.078465.xyz/'},
    {name: 'ghp.arslantu.xyz', url: 'https://ghp.arslantu.xyz/'},
    {name: 'ghp.keleyaa.com', url: 'https://ghp.keleyaa.com/'},
    {name: 'ghpr.cc', url: 'https://ghpr.cc/'},
    {name: 'ghproxy.1888866.xyz', url: 'https://ghproxy.1888866.xyz/'},
    {name: 'ghproxy.cxkpro.top', url: 'https://ghproxy.cxkpro.top/'},
    {name: 'ghproxy.felicity.land', url: 'https://ghproxy.felicity.land/'},
    {name: 'ghproxy.imciel.com', url: 'https://ghproxy.imciel.com/'},
    {name: 'ghproxy.monkeyray.net', url: 'https://ghproxy.monkeyray.net/'},
    {name: 'gh-proxy.net', url: 'https://gh-proxy.net/'},
    {name: 'ghpxy.hwinzniej.top', url: 'https://ghpxy.hwinzniej.top/'},
    {name: 'git.669966.xyz', url: 'https://git.669966.xyz/'},
    {name: 'githubdog.com', url: 'https://githubdog.com/'},
    {name: 'gitproxy.127731.xyz', url: 'https://gitproxy.127731.xyz/'},
    {name: 'gitproxy.click', url: 'https://gitproxy.click/'},
    {name: 'gitproxy.mrhjx.cn', url: 'https://gitproxy.mrhjx.cn/'},
    {name: 'gp.zkitefly.eu.org', url: 'https://gp.zkitefly.eu.org/'},
    {name: 'js.jiangss.shop', url: 'https://js.jiangss.shop/'},
    {name: 'proxy.yaoyaoling.net', url: 'https://proxy.yaoyaoling.net/'},
    {name: 'slink.ltd', url: 'https://slink.ltd/'},
    {name: 'xsadwsd.kdns.fr', url: 'https://xsadwsd.kdns.fr/'},
    {name: '直接访问', url: ''}
];

// 测速目标文件 - 使用小文件提高测速速度
const testFile = 'https://github.com/microsoft/terminal/releases/download/v1.22.10731.0/Microsoft.WindowsTerminal_1.22.10731.0_x64.zip';

// 默认测速超时时间（毫秒）
// 注意：原生fetch()并不支持传入timeout参数（那是axios的写法），
// 之前的 { timeout: 2000 } 实际上被浏览器直接忽略，导致卡住的代理会
// 一直挂到浏览器默认的网络超时（可能长达一二十秒甚至更久），这才是
// "等待时间太长"的根本原因。这里改用 AbortController 实现真正生效的超时。
const DEFAULT_TIMEOUT_MS = 2000;

// 测速函数
export async function testProxySpeed(proxy, timeoutMs = DEFAULT_TIMEOUT_MS) {
    const startTime = performance.now();
    const controller = new AbortController();
    // 到时间强制中断这个请求，不再傻等
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
    
    try {
        let requestUrl;
        
        // 构建请求URL：根据不同代理应用不同的规则
        if (proxy.url) {
            if (proxy.url === 'https://raw.bgithub.xyz/') {
                // 对于bgithub代理，应用特殊规则
                if (testFile.includes('https://raw.githubusercontent.com/')) {
                    requestUrl = testFile.replace(/^(.*?)(https:\/\/raw\.githubusercontent\.com\/)/, 'https://raw.bgithub.xyz/');
                } else if (testFile.includes('https://raw.github.com/')) {
                    requestUrl = testFile.replace(/^(.*?)(https:\/\/raw\.github\.com\/)/, 'https://raw.bgithub.xyz/');
                } else if (testFile.includes('https://github.com/')) {
                    requestUrl = testFile.replace(/^(.*?)(https:\/\/github\.com\/)/, 'https://bgithub.xyz/');
                } else {
                    requestUrl = proxy.url + testFile;
                }
            } else {
                // 对于其他代理，直接拼接URL
                requestUrl = proxy.url + testFile;
            }
        } else {
            // 直接访问
            requestUrl = testFile;
        }
        
        // 使用HEAD请求减少数据传输，添加禁用缓存选项
        // 注意：去掉了原来的自定义User-Agent请求头——浏览器本来就会忽略/禁止
        // 覆盖这个头，留着它没有任何效果，反而多一个自定义头有触发CORS预检
        // （多一次OPTIONS请求）的风险，白白拖慢测速
        const response = await fetch(requestUrl, {
            method: 'HEAD',
            mode: 'cors',
            cache: 'no-cache', // 禁用缓存，确保每次测试都是新请求
            signal: controller.signal, // 绑定超时控制
            headers: {
                'Accept': '*/*' // 接受所有类型的响应
            }
        });
        
        clearTimeout(timeoutId);
        
        if (!response.ok) {
            return { proxy, speed: -1, error: `HTTP错误: ${response.status}` };
        }
        
        const endTime = performance.now();
        const speed = Math.round(endTime - startTime); // 毫秒
        return { proxy, speed, error: null };
    } catch (error) {
        clearTimeout(timeoutId);
        if (error.name === 'AbortError') {
            return { proxy, speed: -1, error: `超时(>${timeoutMs}ms)` };
        }
        return { proxy, speed: -1, error: error.message };
    }
}

// 批量测速 - 并行测试所有代理，提高速度
// options.timeoutMs  单个代理的测速超时时间（毫秒），默认2000ms。代理再多，
//                     总耗时上限也基本等于这个值（因为是并行测速），不会随
//                     代理数量线性增长。
// options.quickSelect 是否启用"先出结果先用"：默认true。第一个测速成功的
//                     代理会立刻被选中并生效，不用等全部代理都测完；其余
//                     代理仍在后台继续测速，全部完成后再校正为真正最快的那个。
export async function testAllProxies(selector = null, onProxySelectedCallback = null, options = {}) {
    const { timeoutMs = DEFAULT_TIMEOUT_MS, quickSelect = true } = options;
    const results = [];
    let quickSelected = false; // 是否已经完成过快速选择，避免重复触发
    
    const applySelection = (proxy) => {
        if (!selector) return;
        selector.value = proxy.url;
        saveSelectedProxy(proxy.url);
        if (onProxySelectedCallback && typeof onProxySelectedCallback === 'function') {
            onProxySelectedCallback(proxy.url);
        }
    };
    
    // 创建一个Promise数组，并行测试所有代理
    const testPromises = proxyList.map(async (proxy) => {
        try {
            const result = await testProxySpeed(proxy, timeoutMs);
            
            // 更新proxyList，添加测速结果
            proxy.speed = result.speed;
            proxy.error = result.error;
            
            // 如果提供了选择器，立即更新显示（哪怕最终顺序还没排好，也先让用户看到进度）
            if (selector) {
                updateProxySelectorWithSpeed(selector);
                
                // 先出结果先用：第一个测速成功的代理立刻生效，不用死等全部测完
                if (quickSelect && !quickSelected && result.speed > 0) {
                    quickSelected = true;
                    applySelection(proxy);
                }
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
    
    // 等待所有测试完成——由于单个请求有超时上限兜底，这里最长也只会等约
    // timeoutMs左右，不会因为某个代理卡住而被拖到很久
    results.push(...await Promise.all(testPromises));
    
    // 根据测速结果对 proxyList 排序：成功的按速度从快到慢排列，失败/未知的排在最后
    sortProxyListBySpeed();
    
    if (selector) {
        // 按排序后的顺序重新渲染下拉框选项
        populateProxySelector(selector);
        // 重新填充每个选项的测速文本（名称 + 速度/失败提示）
        updateProxySelectorWithSpeed(selector);
        
        // 全部测完后，用真正最快的代理做一次最终校正
        // （快速选择阶段选的只是"第一个测完的"，未必是真正最快的那个）
        const fastestProxy = proxyList.find(proxy => proxy.speed > 0);
        if (fastestProxy) {
            applySelection(fastestProxy);
        }
    }
    
    return results;
}

// 根据测速结果对 proxyList 进行排序
// 规则：测速成功（speed > 0）的代理按速度从快到慢排在前面；
// 测速失败或未测速的代理排在最后，彼此之间保持原有相对顺序
export function sortProxyListBySpeed() {
    proxyList.sort((a, b) => {
        const aOk = typeof a.speed === 'number' && a.speed > 0;
        const bOk = typeof b.speed === 'number' && b.speed > 0;
        
        if (aOk && bOk) {
            return a.speed - b.speed; // 都测速成功，速度快的排前面
        }
        if (aOk && !bOk) return -1; // 只有a成功，a排前面
        if (!aOk && bOk) return 1;  // 只有b成功，b排前面
        return 0; // 都失败/未知，保持原有相对顺序（Array.sort是稳定排序）
    });
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
            // 处理 https://github.com/ 开头的地址，替换为 https://bgithub.xyz/
            proxiedUrl = url.replace(/^(.*?)(https:\/\/github\.com\/)/, 'https://bgithub.xyz/');
        } else if (url.includes('https://raw.github.com/')) {
            // 处理 https://github.com/ 开头的地址，替换为 https://bgithub.xyz/
            proxiedUrl = url.replace(/^(.*?)(https:\/\/raw\.github\.com\/)/, 'https://raw.bgithub.xyz/');
        }  else {
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
