# Crafts Themes Manager & Customization Implementation Plan

We are adding a **Themes Manager** to the owner portal. This allows the owner to change the look and feel of the entire e-commerce platform (both customer storefront and owner dashboard) by selecting one of **10 global standard color themes** inspired by famous public portals (Amazon, Shopify, Etsy, IKEA, Apple, Netflix, GitHub, Target, eBay, and the original Crafts theme).

---

## User Review Required

> [!IMPORTANT]
> **Dynamic CSS Variables Override**: Rather than compiling complex CSS on the fly, our theme manager uses a highly performant and clean design:
> 1. The custom colors (Primary, Primary Hover, Background, Dark Accent, Light Accent, Border) are defined as standard CSS variables in [style.css](file:///d:/Dev/SoffianProject/static/css/style.css).
> 2. A custom Django Context Processor [core/context_processors.py](file:///d:/Dev/SoffianProject/core/context_processors.py) fetches the active theme.
> 3. The base templates load these color values and write an inline `<style>` tag in the `<head>` to override the CSS variable declarations globally in the browser.
>
> This ensures that color theme changes apply instantly across every page with zero loading delays and absolute database efficiency.

---

## Proposed Changes

### 1. Database Model additions

#### [MODIFY] [core/models.py](file:///d:/Dev/SoffianProject/core/models.py)
Add the `Theme` model:
- `name` (CharField)
- `primary_color` (CharField)
- `primary_hover_color` (CharField)
- `bg_color` (CharField)
- `dark_color` (CharField)
- `primary_light_color` (CharField)
- `border_color` (CharField)
- `is_active` (BooleanField, default=False)
- Include a custom `save` method to automatically set all other themes to `is_active=False` when a theme is activated.

### 2. Context Processor Integration

#### [NEW] [context_processors.py](file:///d:/Dev/SoffianProject/core/context_processors.py)
- Implement `theme_processor(request)` to fetch the active theme from the database. It falls back to default "Crafts Classic" values if no active theme is set.

#### [MODIFY] [settings.py](file:///d:/Dev/SoffianProject/crafts_project/settings.py)
- Register `core.context_processors.theme_processor` in `TEMPLATES[0]['OPTIONS']['context_processors']`.

### 3. URL Router additions

#### [MODIFY] [owners/urls.py](file:///d:/Dev/SoffianProject/owners/urls.py)
Register theme management URLs:
- `path('themes/', views.theme_list, name='owner_theme_list')`
- `path('themes/activate/<int:pk>/', views.theme_activate, name='owner_theme_activate')`

### 4. Controller Logic

#### [MODIFY] [owners/views.py](file:///d:/Dev/SoffianProject/owners/views.py)
- Implement `theme_list`: Self-heals the database by checking if themes are empty, and populates the 10 portal-inspired themes (Apple, Amazon, Etsy, Shopify, eBay, IKEA, Netflix, GitHub, Target, and Crafts Classic).
- Implement `theme_activate`: Activates the selected theme, updating all storefront colors instantly, and redirects back to the dashboard with a success toast.

### 5. Layout base overrides

#### [MODIFY] [base.html](file:///d:/Dev/SoffianProject/core/templates/core/base.html) & [base_owner.html](file:///d:/Dev/SoffianProject/owners/templates/owners/base_owner.html)
- Add the inline `<style>` variables override in the `<head>`:
  ```html
  <style>
      :root {
          {% if theme %}
              --color-primary: {{ theme.primary_color }};
              --color-primary-hover: {{ theme.primary_hover_color }};
              --color-bg: {{ theme.bg_color }};
              --color-dark: {{ theme.dark_color }};
              --color-primary-light: {{ theme.primary_light_color }};
              --color-border: {{ theme.border_color }};
          {% endif %}
      }
  </style>
  ```
- Link **Theme Customizer** in the owner sidebar menu.

#### [NEW] [theme_list.html](file:///d:/Dev/SoffianProject/owners/templates/owners/theme_list.html)
- Create a visual themes listing dashboard where the owner can click cards. Each card displays colored circle palettes of the theme's colors, its name, and its corresponding public portal reference, along with activation status switches.

---

## Verification Plan

### Automated Tests
- Create tests in `core/tests.py` verifying:
  - Activating one theme deactivates all other themes.
  - Context processor retrieves the correct active theme colors.

### Manual Verification
- Access `/owners/themes/` as owner.
- Review the 10 pre-loaded themes.
- Click **Activate** on the **Netflix Dark & Crimson** theme.
  - Verify that the entire layout toggles to dark mode (dark background and red headers).
- Click **Activate** on the **Amazon Amber** theme.
  - Verify layout changes to white/light-gray backgrounds and yellow/charcoal headers.
- Verify that changes reflect instantly on the customer storefront as well.
