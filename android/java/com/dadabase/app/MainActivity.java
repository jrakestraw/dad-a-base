package com.dadabase.app;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.view.View;
import android.view.WindowInsets;
import android.webkit.JavascriptInterface;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.window.OnBackInvokedCallback;
import android.window.OnBackInvokedDispatcher;

/** Hosts the Dad-A-Base page, which ships inside the APK as an asset and pulls new jokes from the feed. */
public class MainActivity extends Activity {
    private static final int WOOD = Color.rgb(59, 38, 24);
    private WebView web;
    private Object backCallback; // OnBackInvokedCallback on API 33+; typed as Object so older devices never load the class
    private int insetTop, insetBottom;

    /** Hands the system bar heights to the page as --inset-top / --inset-bottom (CSS px). */
    private void pushInsets() {
        if (web == null) return;
        float d = getResources().getDisplayMetrics().density;
        web.evaluateJavascript("document.documentElement.style.setProperty('--inset-top','" + (insetTop / d) + "px');"
            + "document.documentElement.style.setProperty('--inset-bottom','" + (insetBottom / d) + "px')", null);
    }

    /** Called from the page: opens Android's share sheet with the joke text. */
    public class Bridge {
        @JavascriptInterface
        public void share(final String text) {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    Intent send = new Intent(Intent.ACTION_SEND);
                    send.setType("text/plain");
                    send.putExtra(Intent.EXTRA_TEXT, text);
                    try { startActivity(Intent.createChooser(send, "Share this dad joke")); } catch (Exception ignored) { }
                }
            });
        }
    }

    @Override
    @SuppressWarnings("deprecation")
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        web = new WebView(this);
        web.setBackgroundColor(WOOD);
        web.setOverScrollMode(View.OVER_SCROLL_NEVER);
        setContentView(web);

        // From target API 35 the app always draws edge to edge, so the page pads itself clear of the bars.
        if (Build.VERSION.SDK_INT >= 30) getWindow().setDecorFitsSystemWindows(false);
        web.setOnApplyWindowInsetsListener(new View.OnApplyWindowInsetsListener() {
            @Override
            public WindowInsets onApplyWindowInsets(View v, WindowInsets insets) {
                if (Build.VERSION.SDK_INT >= 30) {
                    android.graphics.Insets i = insets.getInsets(WindowInsets.Type.systemBars() | WindowInsets.Type.displayCutout());
                    insetTop = i.top; insetBottom = i.bottom;
                } else {
                    insetTop = insets.getSystemWindowInsetTop(); insetBottom = insets.getSystemWindowInsetBottom();
                }
                pushInsets();
                return insets;
            }
        });

        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setMediaPlaybackRequiresUserGesture(false);
        s.setSupportZoom(false);
        s.setTextZoom(100);
        web.addJavascriptInterface(new Bridge(), "DadBridge");
        web.setWebChromeClient(new WebChromeClient());
        web.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                Uri u = request.getUrl();
                if ("file".equals(u.getScheme())) return false;
                try { startActivity(new Intent(Intent.ACTION_VIEW, u)); } catch (Exception ignored) { }
                return true;
            }

            @Override
            public void onPageFinished(WebView view, String url) { pushInsets(); }
        });
        web.loadUrl("file:///android_asset/index.html");
        if (Build.VERSION.SDK_INT >= 33) registerBack();
    }

    /** Android 13+ (and always from target API 36): back arrives through OnBackInvokedDispatcher, not onBackPressed. */
    private void registerBack() {
        OnBackInvokedCallback cb = new OnBackInvokedCallback() {
            @Override
            public void onBackInvoked() { handleBack(); }
        };
        getOnBackInvokedDispatcher().registerOnBackInvokedCallback(OnBackInvokedDispatcher.PRIORITY_DEFAULT, cb);
        backCallback = cb;
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (web != null) web.onResume();
    }

    @Override
    protected void onPause() {
        if (web != null) web.onPause();
        super.onPause();
    }

    @Override
    protected void onDestroy() {
        if (Build.VERSION.SDK_INT >= 33 && backCallback != null) getOnBackInvokedDispatcher().unregisterOnBackInvokedCallback((OnBackInvokedCallback) backCallback);
        if (web != null) { web.destroy(); web = null; }
        super.onDestroy();
    }

    /** Android 12 and older. */
    @Override
    @SuppressWarnings("deprecation")
    public void onBackPressed() { handleBack(); }

    /** Back returns from the Saved tab first; on the joke screen it leaves the app. */
    private void handleBack() {
        if (web == null) { finish(); return; }
        web.evaluateJavascript("(window.DadABase && window.DadABase.back) ? String(window.DadABase.back()) : 'false'", new ValueCallback<String>() {
            @Override
            public void onReceiveValue(String value) {
                if (value == null || !value.contains("true")) finish();
            }
        });
    }
}
