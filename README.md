# Site da Souvrin

Site estático publicado pelo GitHub Pages em https://www.souvrin.com.br (mesmo modelo do `adedabliu/shield-site`).

- Páginas fixas: `_blog/paginas/*.html` (home, privacidade, 404).
- Blog (/conteudo/): `_blog/posts/AAAA-MM-DD-slug.md`.
- Gerar tudo: `python3 _blog/build.py` (só biblioteca padrão). Gera páginas, blog, feed e sitemap.
- Visual: `assets/site.css` + `_blog/molde.html`. Formulário do simulador envia pelo WhatsApp (sem backend).
- Plano do blog e regra de conteúdo espelhado com a Shield: `_blog/PLANO.md`.
- Fotos: `assets/fotos/` (WebP). Todo post novo usa `imagem:` e `imagem_alt:` no cabeçalho.
