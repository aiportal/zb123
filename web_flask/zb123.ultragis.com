

proxy_cache_path  /prj/tmp/cache  levels=1:2  keys_zone=CACHE:10m  inactive=7d  max_size=5g  use_temp_path=off;

server {
    listen          80;
    server_name     zb123.ultragis.com;

    # gzip on;
    # gzip_comp_level 2;
    # gzip_types text/plain application/json application/javascript application/x-javascript text/css application/xml text/javascript;
    # gzip_vary on;

    proxy_set_header        Host        $http_host;
    proxy_set_header        X-Scheme    $scheme;
    proxy_set_header        X-Real-IP   $remote_addr;

    include     uwsgi_params;
    set $base_url   127.0.0.1:5001;

    location / {
        uwsgi_pass          $base_url;
    }

    location ^~ /static/ {
        root                    /prj/tmp/www;
        error_page              404 = @static;
        expires                 7d;
        add_header              server_cache on;
    }
    location @static {
        internal;

        uwsgi_pass              $base_url;
        proxy_store             on;
        proxy_store_access      user:rw group:rw all:r;
        proxy_temp_path         /prj/tmp/www;
        root                    /prj/tmp/www;
    }
    location ^~ /api/v3/titles {
        uwsgi_pass                  $base_url;

        proxy_cache                 CACHE;
        proxy_cache_key             "$host$request_uri";
        proxy_cache_lock            on;
        proxy_cache_lock_timeout    10s;

        proxy_cache_valid           200 1d;
        # proxy_cache_use_stale       error timeout updating http_500 http_502 http_503 http_504;

        # 客户端缓存
        if ($arg_day ~ "^\d{4}-\d{2}-\d{2}$") {
            expires                 3d;
        }
        add_header                  server_cache on;
    }
    location ^~ /api/v3/content/ {
        uwsgi_pass                  $base_url;

        # proxy_cache                 CACHE;
        # proxy_cache_lock            on;
        # proxy_cache_lock_timeout    10s;
        # proxy_cache_valid           200 7d;
        expires                     7d;
        add_header                  server_cache off;
    }
}

