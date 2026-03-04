import dash
from dash import dcc, html, Input, Output, callback, clientside_callback
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import pandas as pd
from datetime import datetime
import json

app = dash.Dash(
    __name__,
    assets_folder="assets",
    suppress_callback_exceptions=True,
    title="ControllerProfiler"
)

# ─────────────────────────────────────────────
# MOCK DATA
# ─────────────────────────────────────────────
np.random.seed(42)
N = 60

cluster_centers = {
    0: (2.0, 1.5),   # Agressif
    1: (-2.0, 1.0),  # Prudent
    2: (0.5, -2.5),  # Précis
    3: (-0.5, 2.5),  # Chaotique
}
cluster_names = {0: "Agressif", 1: "Prudent", 2: "Précis", 3: "Chaotique"}
cluster_colors_map = {
    0: "#FF4C6A",
    1: "#00E5FF",
    2: "#69FF47",
    3: "#FFB800",
}

umap_x, umap_y, labels, player_names = [], [], [], []
mock_players = [
    "Thomas", "Emma", "Lucas", "Léa", "Noah", "Chloé",
    "Ethan", "Inès", "Hugo", "Camille", "Théo", "Jade",
    "Louis", "Manon", "Nathan", "Alice", "Axel", "Lucie",
    "Maxime", "Sarah", "Raphaël"
]
for i in range(N):
    c = i % 4
    cx, cy = cluster_centers[c]
    umap_x.append(cx + np.random.randn() * 0.6)
    umap_y.append(cy + np.random.randn() * 0.6)
    labels.append(c)
    player_names.append(mock_players[i % len(mock_players)])

df_umap = pd.DataFrame({
    "x": umap_x, "y": umap_y,
    "cluster": [cluster_names[l] for l in labels],
    "player": player_names,
    "color": [cluster_colors_map[l] for l in labels],
})

features = ["Réactivité", "Agressivité", "Fluidité", "Précision", "Prise de risque", "Consistance"]
radar_profiles = {
    "Agressif":  [0.4, 0.95, 0.5, 0.6, 0.9, 0.5],
    "Prudent":   [0.8, 0.2, 0.75, 0.85, 0.2, 0.9],
    "Précis":    [0.9, 0.5, 0.9, 0.95, 0.5, 0.85],
    "Chaotique": [0.6, 0.8, 0.3, 0.4, 0.85, 0.3],
}

# ─────────────────────────────────────────────
# THEMES
# ─────────────────────────────────────────────
THEMES = {
    "cyberpunk": {
        "name": "⚡ Cyberpunk",
        "bg": "#0A0A0F",
        "sidebar": "#0D0D1A",
        "card": "#12121F",
        "border": "#7B2FBE",
        "accent1": "#C724B1",
        "accent2": "#00F5FF",
        "accent3": "#FF4C6A",
        "text": "#E8E8FF",
        "subtext": "#8888AA",
        "font": "'Orbitron', monospace",
        "font_body": "'Share Tech Mono', monospace",
        "glow": "0 0 20px rgba(199,36,177,0.4)",
        "gradient": "linear-gradient(135deg, #C724B1 0%, #00F5FF 100%)",
    },
    "scientific": {
        "name": "🔬 Scientific",
        "bg": "#0B1120",
        "sidebar": "#0E1628",
        "card": "#111C35",
        "border": "#1E3A5F",
        "accent1": "#2979FF",
        "accent2": "#00BCD4",
        "accent3": "#FF6B35",
        "text": "#E3EAF4",
        "subtext": "#7A90B0",
        "font": "'Exo 2', sans-serif",
        "font_body": "'IBM Plex Mono', monospace",
        "glow": "0 0 20px rgba(41,121,255,0.3)",
        "gradient": "linear-gradient(135deg, #2979FF 0%, #00BCD4 100%)",
    },
    "matrix": {
        "name": "🟢 Matrix",
        "bg": "#030A03",
        "sidebar": "#050F05",
        "card": "#071207",
        "border": "#0D3B0D",
        "accent1": "#00FF41",
        "accent2": "#39FF14",
        "accent3": "#ADFF2F",
        "text": "#C8FFC8",
        "subtext": "#4A8A4A",
        "font": "'VT323', monospace",
        "font_body": "'Courier Prime', monospace",
        "glow": "0 0 20px rgba(0,255,65,0.4)",
        "gradient": "linear-gradient(135deg, #00FF41 0%, #39FF14 100%)",
    },
    "datasci": {
        "name": "📊 DataSci",
        "bg": "#0F0E17",
        "sidebar": "#13121F",
        "card": "#1A1929",
        "border": "#2D2B45",
        "accent1": "#FF6B35",
        "accent2": "#F7C59F",
        "accent3": "#FFFFFE",
        "text": "#FFFFFE",
        "subtext": "#A7A9BE",
        "font": "'Syne', sans-serif",
        "font_body": "'Space Mono', monospace",
        "glow": "0 0 20px rgba(255,107,53,0.35)",
        "gradient": "linear-gradient(135deg, #FF6B35 0%, #F7C59F 100%)",
    },
}

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def make_card(children, theme, style_extra=None):
    t = THEMES[theme]
    style = {
        "background": t["card"],
        "border": f"1px solid {t['border']}",
        "borderRadius": "12px",
        "padding": "20px",
        "boxShadow": t["glow"],
    }
    if style_extra:
        style.update(style_extra)
    return html.Div(children, style=style)

def stat_card(label, value, delta, theme):
    t = THEMES[theme]
    return make_card([
        html.Div(label, style={"color": t["subtext"], "fontSize": "11px", "textTransform": "uppercase", "letterSpacing": "2px", "marginBottom": "8px"}),
        html.Div(value, style={"color": t["accent1"], "fontSize": "28px", "fontWeight": "700", "fontFamily": t["font"]}),
        html.Div(delta, style={"color": t["accent2"], "fontSize": "12px", "marginTop": "4px"}),
    ], theme, {"flex": "1", "minWidth": "140px"})

# ─────────────────────────────────────────────
# FIGURES
# ─────────────────────────────────────────────
def make_umap_fig(theme):
    t = THEMES[theme]
    fig = go.Figure()
    for cname, color in [("Agressif", "#FF4C6A"), ("Prudent", "#00E5FF"), ("Précis", "#69FF47"), ("Chaotique", "#FFB800")]:
        mask = df_umap["cluster"] == cname
        fig.add_trace(go.Scatter(
            x=df_umap[mask]["x"], y=df_umap[mask]["y"],
            mode="markers+text",
            name=cname,
            text=df_umap[mask]["player"],
            textposition="top center",
            textfont=dict(size=8, color=color),
            marker=dict(size=10, color=color, opacity=0.85,
                        line=dict(width=1, color="white"),
                        symbol="circle"),
            hovertemplate="<b>%{text}</b><br>Cluster: " + cname + "<extra></extra>",
        ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=t["text"], family=t["font_body"]),
        legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=t["border"], borderwidth=1),
        xaxis=dict(showgrid=True, gridcolor=t["border"], zeroline=False, title="UMAP-1"),
        yaxis=dict(showgrid=True, gridcolor=t["border"], zeroline=False, title="UMAP-2"),
        margin=dict(l=20, r=20, t=20, b=20),
        height=380,
    )
    return fig

def make_radar_fig(profile_name, theme):
    t = THEMES[theme]
    vals = radar_profiles.get(profile_name, radar_profiles["Précis"])
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=vals + [vals[0]],
        theta=features + [features[0]],
        fill="toself",
        fillcolor=f"rgba({int(t['accent1'][1:3],16)},{int(t['accent1'][3:5],16)},{int(t['accent1'][5:7],16)},0.25)",
        line=dict(color=t["accent1"], width=2),
        name=profile_name,
    ))
    fig.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True, range=[0, 1], gridcolor=t["border"], color=t["subtext"]),
            angularaxis=dict(gridcolor=t["border"], color=t["text"]),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color=t["text"], family=t["font_body"]),
        margin=dict(l=30, r=30, t=30, b=30),
        height=300,
        showlegend=False,
    )
    return fig

def make_live_inputs_fig(theme):
    t = THEMES[theme]
    ts = np.linspace(0, 10, 200)
    signals = {
        "Joystick X": np.sin(ts * 2.1) * 0.8 + np.random.randn(200) * 0.05,
        "Joystick Y": np.cos(ts * 1.7) * 0.6 + np.random.randn(200) * 0.05,
        "Gâchette R": np.clip(np.sin(ts * 3) * 0.5 + 0.5, 0, 1),
    }
    colors = [t["accent1"], t["accent2"], t["accent3"]]
    fig = go.Figure()
    for (name, sig), color in zip(signals.items(), colors):
        fig.add_trace(go.Scatter(
            x=ts, y=sig, name=name,
            line=dict(color=color, width=2),
            mode="lines",
        ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=t["text"], family=t["font_body"]),
        xaxis=dict(showgrid=True, gridcolor=t["border"], zeroline=False, title="Temps (s)"),
        yaxis=dict(showgrid=True, gridcolor=t["border"], zeroline=False, range=[-1.1, 1.1]),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=20, r=20, t=10, b=20),
        height=220,
    )
    return fig

def make_reaction_hist(theme):
    t = THEMES[theme]
    data = np.concatenate([
        np.random.normal(180, 20, 30),
        np.random.normal(240, 30, 25),
        np.random.normal(310, 25, 20),
    ])
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=data, nbinsx=25,
        marker_color=t["accent1"],
        opacity=0.8,
        name="Réaction (ms)"
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=t["text"], family=t["font_body"]),
        xaxis=dict(showgrid=False, gridcolor=t["border"], title="Temps de réaction (ms)"),
        yaxis=dict(showgrid=True, gridcolor=t["border"]),
        margin=dict(l=20, r=20, t=10, b=20),
        height=220,
        showlegend=False,
        bargap=0.05,
    )
    return fig

def make_agent_comparison(theme):
    t = THEMES[theme]
    cats = ["Réactivité", "Précision", "Fluidité", "Agressivité", "Consistance"]
    human = [0.72, 0.65, 0.80, 0.55, 0.68]
    agent = [0.69, 0.67, 0.77, 0.58, 0.71]
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Humain", x=cats, y=human, marker_color=t["accent2"], opacity=0.85))
    fig.add_trace(go.Bar(name="Agent IA", x=cats, y=agent, marker_color=t["accent1"], opacity=0.85))
    fig.update_layout(
        barmode="group",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=t["text"], family=t["font_body"]),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor=t["border"], range=[0, 1]),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=20, r=20, t=10, b=20),
        height=250,
    )
    return fig

# ─────────────────────────────────────────────
# PAGES
# ─────────────────────────────────────────────
def page_game(theme):
    t = THEMES[theme]
    return html.Div([
        html.Div([
            html.Div("🎮 Session Live", style={"color": t["accent1"], "fontSize": "22px", "fontWeight": "700", "fontFamily": t["font"], "marginBottom": "4px"}),
            html.Div("Capture des inputs manette en temps réel", style={"color": t["subtext"], "fontSize": "13px"}),
        ], style={"marginBottom": "24px"}),

        # Stats row
        html.Div([
            stat_card("Joueur actif", "Thomas", "▲ Session #3", theme),
            stat_card("Réaction moy.", "187 ms", "▼ -12ms vs avg", theme),
            stat_card("Frames capturés", "4 821", "↑ 60 fps", theme),
            stat_card("Score", "2 340", "▲ +340 pts", theme),
        ], style={"display": "flex", "gap": "16px", "marginBottom": "24px", "flexWrap": "wrap"}),

        # Game zone + live inputs
        html.Div([
            make_card([
                html.Div("Zone de jeu", style={"color": t["subtext"], "fontSize": "11px", "textTransform": "uppercase", "letterSpacing": "2px", "marginBottom": "12px"}),
                html.Div([
                    html.Div("🕹️", style={"fontSize": "60px", "marginBottom": "12px"}),
                    html.Div("PYGAME s'affiche ici", style={
                        "color": t["accent1"], "fontFamily": t["font"], "fontSize": "16px",
                        "border": f"2px dashed {t['accent1']}", "padding": "40px 60px",
                        "borderRadius": "8px", "opacity": "0.6",
                    }),
                    html.Div("→ La fenêtre pygame sera intégrée ou lancée en parallèle", style={"color": t["subtext"], "fontSize": "11px", "marginTop": "12px"}),
                ], style={"textAlign": "center", "padding": "20px"}),
            ], theme, {"flex": "1"}),

            html.Div([
                make_card([
                    html.Div("Inputs manette (live)", style={"color": t["subtext"], "fontSize": "11px", "textTransform": "uppercase", "letterSpacing": "2px", "marginBottom": "12px"}),
                    dcc.Graph(figure=make_live_inputs_fig(theme), config={"displayModeBar": False}),
                ], theme, {"marginBottom": "16px"}),
                make_card([
                    html.Div("Distribution réactions", style={"color": t["subtext"], "fontSize": "11px", "textTransform": "uppercase", "letterSpacing": "2px", "marginBottom": "12px"}),
                    dcc.Graph(figure=make_reaction_hist(theme), config={"displayModeBar": False}),
                ], theme),
            ], style={"flex": "1", "display": "flex", "flexDirection": "column", "gap": "0"}),
        ], style={"display": "flex", "gap": "16px", "flexWrap": "wrap"}),

        # Controls
        html.Div([
            make_card([
                html.Div("Contrôles session", style={"color": t["subtext"], "fontSize": "11px", "textTransform": "uppercase", "letterSpacing": "2px", "marginBottom": "16px"}),
                html.Div([
                    html.Div([
                        html.Div("Nom du joueur", style={"color": t["subtext"], "fontSize": "11px", "marginBottom": "6px"}),
                        dcc.Input(placeholder="ex: Thomas", style={
                            "background": t["bg"], "border": f"1px solid {t['border']}",
                            "color": t["text"], "padding": "8px 12px", "borderRadius": "6px",
                            "fontFamily": t["font_body"], "width": "180px",
                        }),
                    ]),
                    html.Button("▶ DÉMARRER", style={
                        "background": t["gradient"], "border": "none", "color": "#000",
                        "padding": "10px 24px", "borderRadius": "6px", "cursor": "pointer",
                        "fontFamily": t["font"], "fontSize": "13px", "fontWeight": "700",
                        "letterSpacing": "2px",
                    }),
                    html.Button("⏹ ARRÊTER", style={
                        "background": "transparent", "border": f"1px solid {t['accent3']}",
                        "color": t["accent3"], "padding": "10px 24px", "borderRadius": "6px",
                        "cursor": "pointer", "fontFamily": t["font"], "fontSize": "13px",
                        "letterSpacing": "2px",
                    }),
                    html.Button("💾 SAUVEGARDER", style={
                        "background": "transparent", "border": f"1px solid {t['border']}",
                        "color": t["subtext"], "padding": "10px 24px", "borderRadius": "6px",
                        "cursor": "pointer", "fontFamily": t["font"], "fontSize": "13px",
                        "letterSpacing": "2px",
                    }),
                ], style={"display": "flex", "gap": "12px", "alignItems": "flex-end", "flexWrap": "wrap"}),
            ], theme),
        ], style={"marginTop": "16px"}),
    ])


def page_profils(theme):
    t = THEMES[theme]
    return html.Div([
        html.Div([
            html.Div("🧬 Profils comportementaux", style={"color": t["accent1"], "fontSize": "22px", "fontWeight": "700", "fontFamily": t["font"], "marginBottom": "4px"}),
            html.Div("Clustering UMAP — 21 joueurs, 4 profils identifiés", style={"color": t["subtext"], "fontSize": "13px"}),
        ], style={"marginBottom": "24px"}),

        # Stats
        html.Div([
            stat_card("Joueurs analysés", "21", "Toute la classe", theme),
            stat_card("Clusters", "4", "K-Means optimal", theme),
            stat_card("Silhouette score", "0.73", "▲ Bon clustering", theme),
            stat_card("Features", "7", "Comportementales", theme),
        ], style={"display": "flex", "gap": "16px", "marginBottom": "24px", "flexWrap": "wrap"}),

        # UMAP + Radar
        html.Div([
            make_card([
                html.Div("Projection UMAP 2D", style={"color": t["subtext"], "fontSize": "11px", "textTransform": "uppercase", "letterSpacing": "2px", "marginBottom": "12px"}),
                dcc.Graph(id="umap-graph", figure=make_umap_fig(theme), config={"displayModeBar": False}),
            ], theme, {"flex": "2"}),

            make_card([
                html.Div("Profil sélectionné", style={"color": t["subtext"], "fontSize": "11px", "textTransform": "uppercase", "letterSpacing": "2px", "marginBottom": "12px"}),
                dcc.Dropdown(
                    id="profile-selector",
                    options=[{"label": p, "value": p} for p in ["Agressif", "Prudent", "Précis", "Chaotique"]],
                    value="Précis",
                    style={"background": t["card"], "color": t["text"], "border": f"1px solid {t['border']}", "borderRadius": "6px", "marginBottom": "12px"},
                    className="custom-dropdown",
                ),
                dcc.Graph(id="radar-graph", figure=make_radar_fig("Précis", theme), config={"displayModeBar": False}),
                html.Div([
                    html.Div([
                        html.Span("● Agressif  ", style={"color": "#FF4C6A", "fontFamily": t["font_body"], "fontSize": "12px"}),
                        html.Span("● Prudent  ", style={"color": "#00E5FF", "fontFamily": t["font_body"], "fontSize": "12px"}),
                    ]),
                    html.Div([
                        html.Span("● Précis  ", style={"color": "#69FF47", "fontFamily": t["font_body"], "fontSize": "12px"}),
                        html.Span("● Chaotique", style={"color": "#FFB800", "fontFamily": t["font_body"], "fontSize": "12px"}),
                    ]),
                ], style={"marginTop": "8px"}),
            ], theme, {"flex": "1"}),
        ], style={"display": "flex", "gap": "16px", "flexWrap": "wrap"}),

        # Feature table placeholder
        html.Div([
            make_card([
                html.Div("Features moyennes par cluster", style={"color": t["subtext"], "fontSize": "11px", "textTransform": "uppercase", "letterSpacing": "2px", "marginBottom": "16px"}),
                html.Table([
                    html.Thead(html.Tr([
                        html.Th(col, style={"color": t["subtext"], "fontSize": "11px", "padding": "8px 12px", "textAlign": "left", "borderBottom": f"1px solid {t['border']}"})
                        for col in ["Profil", "Réactivité", "Agressivité", "Fluidité", "Précision", "Risque", "Consistance", "Nb joueurs"]
                    ])),
                    html.Tbody([
                        html.Tr([
                            html.Td(v, style={"color": t["text"] if i > 0 else color, "padding": "8px 12px", "fontFamily": t["font_body"], "fontSize": "13px", "borderBottom": f"1px solid {t['border']}"})
                            for i, v in enumerate(row)
                        ])
                        for row, color in [
                            (["Agressif",  "0.40", "0.95", "0.50", "0.60", "0.90", "0.50", "6"], "#FF4C6A"),
                            (["Prudent",   "0.80", "0.20", "0.75", "0.85", "0.20", "0.90", "5"], "#00E5FF"),
                            (["Précis",    "0.90", "0.50", "0.90", "0.95", "0.50", "0.85", "5"], "#69FF47"),
                            (["Chaotique", "0.60", "0.80", "0.30", "0.40", "0.85", "0.30", "5"], "#FFB800"),
                        ]
                    ]),
                ], style={"width": "100%", "borderCollapse": "collapse"}),
            ], theme),
        ], style={"marginTop": "16px"}),
    ])


def page_classifier(theme):
    t = THEMES[theme]
    return html.Div([
        html.Div([
            html.Div("🎯 Classificateur", style={"color": t["accent1"], "fontSize": "22px", "fontWeight": "700", "fontFamily": t["font"], "marginBottom": "4px"}),
            html.Div("Identification du profil d'un nouveau joueur en temps réel", style={"color": t["subtext"], "fontSize": "13px"}),
        ], style={"marginBottom": "24px"}),

        html.Div([
            # Input panel
            make_card([
                html.Div("Nouveau joueur", style={"color": t["subtext"], "fontSize": "11px", "textTransform": "uppercase", "letterSpacing": "2px", "marginBottom": "16px"}),

                html.Div("Nom", style={"color": t["subtext"], "fontSize": "11px", "marginBottom": "6px"}),
                dcc.Input(placeholder="ex: Nouveau joueur", style={
                    "background": t["bg"], "border": f"1px solid {t['border']}",
                    "color": t["text"], "padding": "8px 12px", "borderRadius": "6px",
                    "fontFamily": t["font_body"], "width": "100%", "marginBottom": "16px",
                }),

                *[html.Div([
                    html.Div(f"{feat}", style={"color": t["subtext"], "fontSize": "11px", "marginBottom": "4px", "display": "flex", "justifyContent": "space-between"}),
                    dcc.Slider(0, 1, 0.01, value=round(np.random.uniform(0.3, 0.9), 2),
                               marks=None, tooltip={"placement": "bottom"},
                               className="custom-slider"),
                    html.Div(style={"marginBottom": "12px"}),
                ]) for feat in features],

                html.Button("🔍 CLASSIFIER", style={
                    "background": t["gradient"], "border": "none", "color": "#000",
                    "padding": "12px 32px", "borderRadius": "6px", "cursor": "pointer",
                    "fontFamily": t["font"], "fontSize": "14px", "fontWeight": "700",
                    "letterSpacing": "2px", "width": "100%", "marginTop": "8px",
                }),
            ], theme, {"flex": "1"}),

            # Result panel
            html.Div([
                make_card([
                    html.Div("Résultat", style={"color": t["subtext"], "fontSize": "11px", "textTransform": "uppercase", "letterSpacing": "2px", "marginBottom": "16px"}),
                    html.Div([
                        html.Div("PROFIL IDENTIFIÉ", style={"color": t["subtext"], "fontSize": "11px", "letterSpacing": "2px"}),
                        html.Div("🎯 PRÉCIS", style={"color": t["accent1"], "fontSize": "36px", "fontFamily": t["font"], "fontWeight": "700", "marginTop": "8px"}),
                        html.Div("Confiance : 87%", style={"color": t["accent2"], "fontSize": "14px", "marginTop": "4px"}),
                    ], style={"textAlign": "center", "padding": "20px 0"}),

                    # Confidence bars
                    html.Div([
                        html.Div([
                            html.Div([
                                html.Span(p, style={"color": c, "fontFamily": t["font_body"], "fontSize": "12px"}),
                                html.Span(f"{v}%", style={"color": t["subtext"], "fontSize": "12px"}),
                            ], style={"display": "flex", "justifyContent": "space-between", "marginBottom": "4px"}),
                            html.Div(html.Div(style={
                                "width": f"{v}%", "height": "6px",
                                "background": c, "borderRadius": "3px",
                                "transition": "width 0.5s ease",
                            }), style={"background": t["border"], "borderRadius": "3px", "marginBottom": "10px"}),
                        ])
                        for p, v, c in [("Précis", 87, "#69FF47"), ("Prudent", 8, "#00E5FF"), ("Agressif", 3, "#FF4C6A"), ("Chaotique", 2, "#FFB800")]
                    ]),
                ], theme, {"marginBottom": "16px"}),

                make_card([
                    html.Div("Radar comparatif", style={"color": t["subtext"], "fontSize": "11px", "textTransform": "uppercase", "letterSpacing": "2px", "marginBottom": "8px"}),
                    dcc.Graph(figure=make_radar_fig("Précis", theme), config={"displayModeBar": False}),
                ], theme),
            ], style={"flex": "1", "display": "flex", "flexDirection": "column"}),
        ], style={"display": "flex", "gap": "16px", "flexWrap": "wrap"}),
    ])


def page_agent(theme):
    t = THEMES[theme]
    return html.Div([
        html.Div([
            html.Div("🤖 Agent Imitateur", style={"color": t["accent1"], "fontSize": "22px", "fontWeight": "700", "fontFamily": t["font"], "marginBottom": "4px"}),
            html.Div("L'IA rejoue les patterns comportementaux d'un profil appris", style={"color": t["subtext"], "fontSize": "13px"}),
        ], style={"marginBottom": "24px"}),

        html.Div([
            make_card([
                html.Div("Configuration de l'agent", style={"color": t["subtext"], "fontSize": "11px", "textTransform": "uppercase", "letterSpacing": "2px", "marginBottom": "16px"}),

                html.Div("Profil à imiter", style={"color": t["subtext"], "fontSize": "11px", "marginBottom": "6px"}),
                dcc.Dropdown(
                    options=[{"label": p, "value": p} for p in ["Agressif", "Prudent", "Précis", "Chaotique"]],
                    value="Agressif",
                    style={"background": t["card"], "color": "#000", "borderRadius": "6px", "marginBottom": "16px"},
                ),

                html.Div("Joueur cible (optionnel)", style={"color": t["subtext"], "fontSize": "11px", "marginBottom": "6px"}),
                dcc.Dropdown(
                    options=[{"label": p, "value": p} for p in mock_players],
                    placeholder="Sélectionner un joueur...",
                    style={"background": t["card"], "color": "#000", "borderRadius": "6px", "marginBottom": "16px"},
                ),

                html.Div("Fidélité d'imitation", style={"color": t["subtext"], "fontSize": "11px", "marginBottom": "6px"}),
                dcc.Slider(0, 100, 1, value=80, marks={0: "Libre", 50: "Mixte", 100: "Fidèle"},
                           tooltip={"placement": "bottom"}, className="custom-slider"),

                html.Div(style={"height": "20px"}),

                html.Button("▶ LANCER L'AGENT", style={
                    "background": t["gradient"], "border": "none", "color": "#000",
                    "padding": "12px 32px", "borderRadius": "6px", "cursor": "pointer",
                    "fontFamily": t["font"], "fontSize": "14px", "fontWeight": "700",
                    "letterSpacing": "2px", "width": "100%",
                }),
                html.Div(style={"height": "8px"}),
                html.Button("⏹ ARRÊTER", style={
                    "background": "transparent", "border": f"1px solid {t['accent3']}",
                    "color": t["accent3"], "padding": "10px 32px", "borderRadius": "6px",
                    "cursor": "pointer", "fontFamily": t["font"], "fontSize": "13px",
                    "width": "100%",
                }),
            ], theme, {"flex": "1"}),

            html.Div([
                make_card([
                    html.Div("Comparaison Humain vs Agent IA", style={"color": t["subtext"], "fontSize": "11px", "textTransform": "uppercase", "letterSpacing": "2px", "marginBottom": "12px"}),
                    dcc.Graph(figure=make_agent_comparison(theme), config={"displayModeBar": False}),
                ], theme, {"marginBottom": "16px"}),

                make_card([
                    html.Div("Score de similarité comportementale", style={"color": t["subtext"], "fontSize": "11px", "textTransform": "uppercase", "letterSpacing": "2px", "marginBottom": "16px"}),
                    html.Div([
                        html.Div("92.4%", style={"color": t["accent1"], "fontSize": "48px", "fontFamily": t["font"], "fontWeight": "700", "textAlign": "center"}),
                        html.Div("de similarité avec le profil Agressif", style={"color": t["subtext"], "fontSize": "13px", "textAlign": "center", "marginTop": "4px"}),
                        html.Div([
                            html.Div(style={
                                "width": "92.4%", "height": "8px",
                                "background": t["gradient"], "borderRadius": "4px",
                            }),
                        ], style={"background": t["border"], "borderRadius": "4px", "marginTop": "16px"}),
                    ]),
                ], theme),
            ], style={"flex": "2", "display": "flex", "flexDirection": "column"}),
        ], style={"display": "flex", "gap": "16px", "flexWrap": "wrap"}),
    ])


# ─────────────────────────────────────────────
# LAYOUT
# ─────────────────────────────────────────────
app.layout = html.Div([
    dcc.Store(id="theme-store", data="cyberpunk"),
    dcc.Store(id="page-store", data="game"),

    # Google Fonts
    html.Link(rel="stylesheet", href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Share+Tech+Mono&family=Exo+2:wght@400;700&family=IBM+Plex+Mono&family=VT323&family=Courier+Prime&family=Syne:wght@400;700;800&family=Space+Mono&display=swap"),

    html.Div(id="main-container", children=[
        # SIDEBAR
        html.Div(id="sidebar", children=[
            # Logo
            html.Div([
                html.Div("🎮", style={"fontSize": "28px"}),
                html.Div([
                    html.Div("Controller", style={"fontSize": "14px", "fontWeight": "700", "letterSpacing": "2px"}),
                    html.Div("PROFILER", style={"fontSize": "10px", "letterSpacing": "4px", "opacity": "0.6"}),
                ]),
            ], style={"display": "flex", "alignItems": "center", "gap": "12px", "marginBottom": "32px", "padding": "0 4px"}),

            # Nav
            html.Div("NAVIGATION", style={"fontSize": "9px", "letterSpacing": "3px", "opacity": "0.4", "marginBottom": "12px", "padding": "0 4px"}),
            html.Div([
                html.Button([html.Span("🎮", style={"marginRight": "10px"}), "Live Game"],
                    id="nav-game", n_clicks=0, className="nav-btn active-nav"),
                html.Button([html.Span("🧬", style={"marginRight": "10px"}), "Profils"],
                    id="nav-profils", n_clicks=0, className="nav-btn"),
                html.Button([html.Span("🎯", style={"marginRight": "10px"}), "Classifier"],
                    id="nav-classifier", n_clicks=0, className="nav-btn"),
                html.Button([html.Span("🤖", style={"marginRight": "10px"}), "Agent IA"],
                    id="nav-agent", n_clicks=0, className="nav-btn"),
            ], style={"display": "flex", "flexDirection": "column", "gap": "4px", "marginBottom": "32px"}),

            html.Div("THÈME", style={"fontSize": "9px", "letterSpacing": "3px", "opacity": "0.4", "marginBottom": "12px", "padding": "0 4px"}),
            html.Div([
                html.Button(THEMES[th]["name"], id=f"theme-{th}", n_clicks=0, className="theme-btn",
                    **{"data-theme": th})
                for th in THEMES
            ], style={"display": "flex", "flexDirection": "column", "gap": "4px"}),

            # Footer
            html.Div([
                html.Div("Master SISE 2025–2026", style={"fontSize": "10px", "opacity": "0.4"}),
                html.Div("Projet IA Temps réel", style={"fontSize": "10px", "opacity": "0.4"}),
            ], style={"position": "absolute", "bottom": "24px", "left": "24px"}),
        ]),

        # MAIN CONTENT
        html.Div(id="page-content", style={"flex": "1", "padding": "32px", "overflowY": "auto"}),
    ]),
], id="root")


# ─────────────────────────────────────────────
# CALLBACKS
# ─────────────────────────────────────────────
@app.callback(
    Output("theme-store", "data"),
    [Input(f"theme-{th}", "n_clicks") for th in THEMES],
    prevent_initial_call=True,
)
def update_theme(*args):
    ctx = dash.callback_context
    if not ctx.triggered:
        return "cyberpunk"
    btn_id = ctx.triggered[0]["prop_id"].split(".")[0]
    return btn_id.replace("theme-", "")


@app.callback(
    Output("page-store", "data"),
    [Input("nav-game", "n_clicks"), Input("nav-profils", "n_clicks"),
     Input("nav-classifier", "n_clicks"), Input("nav-agent", "n_clicks")],
    prevent_initial_call=True,
)
def update_page(g, p, c, a):
    ctx = dash.callback_context
    if not ctx.triggered:
        return "game"
    btn = ctx.triggered[0]["prop_id"].split(".")[0]
    return {"nav-game": "game", "nav-profils": "profils", "nav-classifier": "classifier", "nav-agent": "agent"}.get(btn, "game")


@app.callback(
    Output("main-container", "style"),
    Output("sidebar", "style"),
    Output("page-content", "children"),
    Input("theme-store", "data"),
    Input("page-store", "data"),
)
def render_all(theme, page):
    t = THEMES[theme]
    base_font = f"font-family: {t['font_body']};"

    container_style = {
        "display": "flex", "minHeight": "100vh",
        "background": t["bg"], "color": t["text"],
        "fontFamily": t["font_body"],
    }
    sidebar_style = {
        "width": "220px", "minHeight": "100vh",
        "background": t["sidebar"],
        "borderRight": f"1px solid {t['border']}",
        "padding": "24px", "position": "relative",
        "fontFamily": t["font_body"],
    }

    pages = {
        "game": page_game(theme),
        "profils": page_profils(theme),
        "classifier": page_classifier(theme),
        "agent": page_agent(theme),
    }
    content = pages.get(page, page_game(theme))
    return container_style, sidebar_style, content


@app.callback(
    Output("radar-graph", "figure"),
    Input("profile-selector", "value"),
    Input("theme-store", "data"),
)
def update_radar(profile, theme):
    return make_radar_fig(profile or "Précis", theme)


if __name__ == "__main__":
    app.run(debug=True, port=8050)
