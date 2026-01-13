(function() {
    const STORAGE_KEY = 'kaihan_artwork_comments';
    let artworksData = null;
    let currentArtworkId = null;

    function getComments() {
        try {
            const data = localStorage.getItem(STORAGE_KEY);
            return data ? JSON.parse(data) : {};
        } catch (e) {
            return {};
        }
    }

    function saveComments(comments) {
        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(comments));
        } catch (e) {
            console.error('Failed to save comments:', e);
        }
    }

    function getArtworkComments(artworkId) {
        const comments = getComments();
        return comments[artworkId] || { comments: [] };
    }

    function addComment(artworkId, text) {
        if (!text.trim()) return;
        const comments = getComments();
        if (!comments[artworkId]) {
            comments[artworkId] = { comments: [] };
        }
        const now = new Date();
        comments[artworkId].comments.push({
            id: 'c' + Date.now(),
            text: text.trim(),
            timestamp: now.getTime(),
            date: formatDateTime(now)
        });
        saveComments(comments);
    }

    function deleteComment(artworkId, commentId) {
        const comments = getComments();
        if (comments[artworkId]) {
            comments[artworkId].comments = comments[artworkId].comments.filter(c => c.id !== commentId);
            saveComments(comments);
        }
    }

    function formatDateTime(date) {
        const y = date.getFullYear();
        const m = String(date.getMonth() + 1).padStart(2, '0');
        const d = String(date.getDate()).padStart(2, '0');
        const h = String(date.getHours()).padStart(2, '0');
        const min = String(date.getMinutes()).padStart(2, '0');
        return `${y}-${m}-${d} ${h}:${min}`;
    }

    function getMonthKey(timestamp) {
        const date = new Date(timestamp);
        return `${date.getFullYear()}年${String(date.getMonth() + 1).padStart(2, '0')}月`;
    }

    function groupByMonth(artworks) {
        const groups = {};
        artworks.forEach(artwork => {
            const key = getMonthKey(artwork.timestamp);
            if (!groups[key]) {
                groups[key] = [];
            }
            groups[key].push(artwork);
        });
        return groups;
    }

    function getConfidenceClass(confidence) {
        const map = {
            'HIGH': 'confidence-high',
            'MEDIUM': 'confidence-medium',
            'LOW': 'confidence-low'
        };
        return map[confidence] || 'confidence-low';
    }

    function getSourceLabel(source) {
        const map = {
            'EXIF_DATETIME': 'EXIF原始时间',
            'FILENAME_TIMESTAMP': '文件名时间戳',
            'FILENAME_PATTERN': '文件名日期',
            'FILE_MTIME': '文件修改时间',
            'FALLBACK': '默认时间'
        };
        return map[source] || source;
    }

    function getConfidenceLabel(confidence) {
        const map = {
            'HIGH': '高可信度',
            'MEDIUM': '中等可信度',
            'LOW': '低可信度'
        };
        return map[confidence] || confidence;
    }

    function renderStats(data) {
        const statsEl = document.getElementById('stats');
        if (!statsEl || !data.artworks.length) return;
        const oldest = data.artworks[data.artworks.length - 1];
        const newest = data.artworks[0];
        statsEl.innerHTML = `共 ${data.total_count} 幅作品 | ${oldest.date_display} - ${newest.date_display}`;
    }

    function renderTimelineNav(groups) {
        const navEl = document.getElementById('timeline-nav');
        if (!navEl) return;
        const months = Object.keys(groups);
        if (months.length === 0) {
            navEl.style.display = 'none';
            return;
        }
        navEl.innerHTML = months.map(month => 
            `<a href="#section-${month}">${month}</a>`
        ).join('');
    }

    function renderArtworks(data) {
        const container = document.getElementById('artworks-container');
        if (!container) return;
        if (!data.artworks || data.artworks.length === 0) {
            container.innerHTML = `
                <div class="empty-message">
                    <h2>暂无作品</h2>
                    <p>请将书法作品照片放入 <code>images/</code> 目录</p>
                    <p>然后运行 <code>python3 generate.py</code></p>
                </div>
            `;
            return;
        }
        const groups = groupByMonth(data.artworks);
        renderTimelineNav(groups);
        let html = '';
        Object.keys(groups).forEach(month => {
            const artworks = groups[month];
            html += `
                <section class="month-section" id="section-${month}">
                    <h2 class="month-header">${month}</h2>
                    <div class="artworks-grid">
            `;
            artworks.forEach(artwork => {
                const artworkComments = getArtworkComments(artwork.id);
                const commentCount = artworkComments.comments.length;
                // 优先使用第一条评论作为标题，否则使用OCR识别的标题
                const displayTitle = artworkComments.comments.length > 0 
                    ? artworkComments.comments[0].text 
                    : (artwork.title && artwork.title !== '未命名作品' ? artwork.title : '');
                html += `
                    <div class="artwork-card" data-id="${artwork.id}">
                        <div class="artwork-image-container">
                            <img class="artwork-image" 
                                 src="${artwork.path}" 
                                 alt="${displayTitle || artwork.filename}"
                                 loading="lazy">
                        </div>
                        <div class="artwork-info">
                            ${displayTitle ? `<div class="artwork-title">${displayTitle}</div>` : ''}
                            <div class="artwork-date">
                                <span class="confidence-badge ${getConfidenceClass(artwork.confidence)}"></span>
                                ${artwork.date_display}
                            </div>
                            <div class="artwork-comments-count">
                                ${commentCount > 1 ? `💬 ${commentCount - 1} 条评论` : ''}
                            </div>
                        </div>
                    </div>
                `;
            });
            html += `
                    </div>
                </section>
            `;
        });
        container.innerHTML = html;
        container.querySelectorAll('.artwork-card').forEach(card => {
            card.addEventListener('click', () => openModal(card.dataset.id));
        });
    }

    function openModal(artworkId) {
        const artwork = artworksData.artworks.find(a => a.id === artworkId);
        if (!artwork) return;
        currentArtworkId = artworkId;
        const modal = document.getElementById('artwork-modal');
        const modalImage = document.getElementById('modal-image');
        const modalDate = document.getElementById('modal-date');
        const modalSource = document.getElementById('modal-source');
        modalImage.src = artwork.path;
        // 优先使用第一条评论作为标题
        const artworkComments = getArtworkComments(artworkId);
        const displayTitle = artworkComments.comments.length > 0 
            ? artworkComments.comments[0].text 
            : (artwork.title && artwork.title !== '未命名作品' ? artwork.title : '');
        modalDate.textContent = displayTitle 
            ? `${displayTitle} - ${artwork.date_display}` 
            : artwork.date_display;
        modalSource.innerHTML = `
            时间来源: ${getSourceLabel(artwork.time_source)} 
            <span class="confidence-badge ${getConfidenceClass(artwork.confidence)}"></span>
            (${getConfidenceLabel(artwork.confidence)})
        `;
        renderModalComments(artworkId);
        modal.showModal();
    }

    function renderModalComments(artworkId) {
        const commentsContainer = document.getElementById('modal-comments');
        const artworkComments = getArtworkComments(artworkId);
        if (artworkComments.comments.length === 0) {
            commentsContainer.innerHTML = '<p class="no-comments">暂无评论</p>';
            return;
        }
        commentsContainer.innerHTML = artworkComments.comments.map(comment => `
            <div class="comment-item" data-comment-id="${comment.id}">
                <button class="comment-delete" title="删除">&times;</button>
                <div class="comment-text">${escapeHtml(comment.text)}</div>
                <div class="comment-date">${comment.date}</div>
            </div>
        `).join('');
        commentsContainer.querySelectorAll('.comment-delete').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const commentId = btn.closest('.comment-item').dataset.commentId;
                deleteComment(artworkId, commentId);
                renderModalComments(artworkId);
                updateCardCommentCount(artworkId);
            });
        });
    }

    function updateCardCommentCount(artworkId) {
        const card = document.querySelector(`.artwork-card[data-id="${artworkId}"]`);
        if (!card) return;
        const artworkComments = getArtworkComments(artworkId);
        const countEl = card.querySelector('.artwork-comments-count');
        if (countEl) {
            const count = artworkComments.comments.length;
            countEl.textContent = count > 0 ? `💬 ${count} 条评论` : '';
        }
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function initModal() {
        const modal = document.getElementById('artwork-modal');
        const closeBtn = document.getElementById('modal-close');
        const addCommentBtn = document.getElementById('add-comment-btn');
        const commentInput = document.getElementById('comment-input');
        closeBtn.addEventListener('click', () => {
            modal.close();
            currentArtworkId = null;
        });
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.close();
                currentArtworkId = null;
            }
        });
        addCommentBtn.addEventListener('click', () => {
            if (!currentArtworkId) return;
            const text = commentInput.value;
            if (text.trim()) {
                addComment(currentArtworkId, text);
                commentInput.value = '';
                renderModalComments(currentArtworkId);
                updateCardCommentCount(currentArtworkId);
            }
        });
        commentInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                addCommentBtn.click();
            }
        });
    }

    async function loadData() {
        try {
            const response = await fetch('data/artworks.json');
            if (!response.ok) {
                throw new Error('Failed to load artworks data');
            }
            artworksData = await response.json();
            renderStats(artworksData);
            renderArtworks(artworksData);
        } catch (error) {
            console.error('Error loading data:', error);
            const container = document.getElementById('artworks-container');
            container.innerHTML = `
                <div class="empty-message">
                    <h2>加载失败</h2>
                    <p>请确保已运行 <code>python3 generate.py</code> 生成数据</p>
                    <p>或将书法作品照片放入 <code>images/</code> 目录后重新运行脚本</p>
                </div>
            `;
        }
    }

    document.addEventListener('DOMContentLoaded', () => {
        initModal();
        loadData();
    });
})();
