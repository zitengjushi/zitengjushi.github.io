// 导航栏共享组件
// 在各页面中调用 renderNavbar('当前页面文件名') 来渲染导航栏并设置高亮项

const navItems = [
    { href: 'index.html', label: '首页' },
    { href: 'apk.html', label: '应用下载' },
    { href: 'iptv.html', label: '直播线路' },
    { href: 'play.html', label: 'M3U8播放器' },
    { href: 'lx.html', label: '落雪音乐' },
];

function renderNavbar(activePage) {
    const navHtml = `
    <nav class="navbar navbar-expand-lg navbar-light bg-white rounded-3 shadow-sm mb-5 py-3">
        <div class="container">
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav gap-3">
${navItems.map(item => {
    const isActive = item.href === activePage;
    const linkClass = isActive
        ? 'nav-link active btn btn-primary text-white rounded-2'
        : 'nav-link btn btn-outline-primary rounded-2';
    return `                    <li class="nav-item">
                        <a class="${linkClass}" href="${item.href}">${item.label}</a>
                    </li>`;
}).join('\n')}
                </ul>
            </div>
        </div>
    </nav>`;

    const container = document.getElementById('navbar-container');
    if (container) {
        container.innerHTML = navHtml;
    }
}
