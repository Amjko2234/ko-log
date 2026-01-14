import re
from re import Pattern

# -----------------------------------------------------------------------------
#   Remover
# -----------------------------------------------------------------------------


def strip(t: str) -> str:
    """Strip markups ('[bold]...[/bold]') from messages."""

    pattern: Pattern[str] = re.compile(r"\[/?[^\]]*\]")
    return pattern.sub("", t)


# -----------------------------------------------------------------------------
#   Non-colors
# -----------------------------------------------------------------------------


def bold(t: str) -> str:
    """Apply bold style to text."""

    return f"[bold]{t}[/bold]"


def italic(t: str) -> str:
    """Apply italic style to text."""

    return f"[italic]{t}[/italic]"


def underline(t: str) -> str:
    """Apply underline style to text."""

    return f"[underline]{t}[/underline]"


def dim(t: str) -> str:
    """Apply dim style to text."""

    return f"[dim]{t}[/dim]"


# -----------------------------------------------------------------------------
#   Colors
# -----------------------------------------------------------------------------


def black(t: str) -> str:
    """Apply a black color to text."""

    return f"[black]{t}[/black]"


def red(t: str) -> str:
    """Apply a red color to text."""

    return f"[red]{t}[/red]"


def green(t: str) -> str:
    """Apply a green color to text."""

    return f"[green]{t}[/green]"


def yellow(t: str) -> str:
    """Apply a yellow color to text."""

    return f"[yellow]{t}[/yellow]"


def blue(t: str) -> str:
    """Apply a blue color to text."""

    return f"[blue]{t}[/blue]"


def magenta(t: str) -> str:
    """Apply a magenta color to text."""

    return f"[magenta]{t}[/magenta]"


def cyan(t: str) -> str:
    """Apply a cyan color to text."""

    return f"[cyan]{t}[/cyan]"


def white(t: str) -> str:
    """Apply a white color to text."""

    return f"[white]{t}[/white]"


def bright_black(t: str) -> str:
    """Apply a bright_black color to text."""

    return f"[bright_black]{t}[/bright_black]"


def bright_red(t: str) -> str:
    """Apply a bright_red color to text."""

    return f"[bright_red]{t}[/bright_red]"


def bright_green(t: str) -> str:
    """Apply a bright_green color to text."""

    return f"[bright_green]{t}[/bright_green]"


def bright_yellow(t: str) -> str:
    """Apply a bright_yellow color to text."""

    return f"[bright_yellow]{t}[/bright_yellow]"


def bright_blue(t: str) -> str:
    """Apply a bright_blue color to text."""

    return f"[bright_blue]{t}[/bright_blue]"


def bright_magenta(t: str) -> str:
    """Apply a bright_magenta color to text."""

    return f"[bright_magenta]{t}[/bright_magenta]"


def bright_cyan(t: str) -> str:
    """Apply a bright_cyan color to text."""

    return f"[bright_cyan]{t}[/bright_cyan]"


def bright_white(t: str) -> str:
    """Apply a bright_white color to text."""

    return f"[bright_white]{t}[/bright_white]"


def grey0(t: str) -> str:
    """Apply a grey0 color to text."""

    return f"[grey0]{t}[/grey0]"


def navy_blue(t: str) -> str:
    """Apply a navy_blue color to text."""

    return f"[navy_blue]{t}[/navy_blue]"


def dark_blue(t: str) -> str:
    """Apply a dark_blue color to text."""

    return f"[dark_blue]{t}[/dark_blue]"


def blue3(t: str) -> str:
    """Apply a blue3 color to text."""

    return f"[blue3]{t}[/blue3]"


def blue1(t: str) -> str:
    """Apply a blue1 color to text."""

    return f"[blue1]{t}[/blue1]"


def dark_green(t: str) -> str:
    """Apply a dark_green color to text."""

    return f"[dark_green]{t}[/dark_green]"


def deep_sky_b1ue4(t: str) -> str:
    """Apply a deep_sky_b1ue4 color to text."""

    return f"[deep_sky_b1ue4]{t}[/deep_sky_b1ue4]"


def dodger_blue3(t: str) -> str:
    """Apply a dodger_blue3 color to text."""

    return f"[dodger_blue3]{t}[/dodger_blue3]"


def dodger_blue2(t: str) -> str:
    """Apply a dodger_blue2 color to text."""

    return f"[dodger_blue2]{t}[/dodger_blue2]"


def green4(t: str) -> str:
    """Apply a green4 color to text."""

    return f"[green4]{t}[/green4]"


def spring_green4(t: str) -> str:
    """Apply a spring_green4 color to text."""

    return f"[spring_green4]{t}[/spring_green4]"


def turquoise4(t: str) -> str:
    """Apply a turquoise4 color to text."""

    return f"[turquoise4]{t}[/turquoise4]"


def deep_sky_b1ue3(t: str) -> str:
    """Apply a deep_sky_b1ue3 color to text."""

    return f"[deep_sky_b1ue3]{t}[/deep_sky_b1ue3]"


def dodger_bluel(t: str) -> str:
    """Apply a dodger_bluel color to text."""

    return f"[dodger_bluel]{t}[/dodger_bluel]"


def dark_cyan(t: str) -> str:
    """Apply a dark_cyan color to text."""

    return f"[dark_cyan]{t}[/dark_cyan]"


def deep_sky_blue1(t: str) -> str:
    """Apply a deep_sky_blue1 color to text."""

    return f"[deep_sky_blue1]{t}[/deep_sky_blue1]"


def green3(t: str) -> str:
    """Apply a green3 color to text."""

    return f"[green3]{t}[/green3]"


def spring_green3(t: str) -> str:
    """Apply a spring_green3 color to text."""

    return f"[spring_green3]{t}[/spring_green3]"


def cyan3(t: str) -> str:
    """Apply a cyan3 color to text."""

    return f"[cyan3]{t}[/cyan3]"


def dark_turquoise(t: str) -> str:
    """Apply a dark_turquoise color to text."""

    return f"[dark_turquoise]{t}[/dark_turquoise]"


def turquoise2(t: str) -> str:
    """Apply a turquoise2 color to text."""

    return f"[turquoise2]{t}[/turquoise2]"


def green1(t: str) -> str:
    """Apply a green1 color to text."""

    return f"[green1]{t}[/green1]"


def spring_green2(t: str) -> str:
    """Apply a spring_green2 color to text."""

    return f"[spring_green2]{t}[/spring_green2]"


def spring_green1(t: str) -> str:
    """Apply a spring_green1 color to text."""

    return f"[spring_green1]{t}[/spring_green1]"


def medium_spring_green(t: str) -> str:
    """Apply a medium_spring_green color to text."""

    return f"[medium_spring_green]{t}[/medium_spring_green]"


def cyan2(t: str) -> str:
    """Apply a cyan2 color to text."""

    return f"[cyan2]{t}[/cyan2]"


def cyan1(t: str) -> str:
    """Apply a cyan1 color to text."""

    return f"[cyan1]{t}[/cyan1]"


def purple4(t: str) -> str:
    """Apply a purple4 color to text."""

    return f"[purple4]{t}[/purple4]"


def purple3(t: str) -> str:
    """Apply a purple3 color to text."""

    return f"[purple3]{t}[/purple3]"


def blue_violet(t: str) -> str:
    """Apply a blue_violet color to text."""

    return f"[blue_violet]{t}[/blue_violet]"


def grey37(t: str) -> str:
    """Apply a grey37 color to text."""

    return f"[grey37]{t}[/grey37]"


def medium_purple4(t: str) -> str:
    """Apply a medium_purple4 color to text."""

    return f"[medium_purple4]{t}[/medium_purple4]"


def slate_blue3(t: str) -> str:
    """Apply a slate_blue3 color to text."""

    return f"[slate_blue3]{t}[/slate_blue3]"


def royal_blue1(t: str) -> str:
    """Apply a royal_blue1 color to text."""

    return f"[royal_blue1]{t}[/royal_blue1]"


def chartreuse4(t: str) -> str:
    """Apply a chartreuse4 color to text."""

    return f"[chartreuse4]{t}[/chartreuse4]"


def pale_turquoise4(t: str) -> str:
    """Apply a pale_turquoise4 color to text."""

    return f"[pale_turquoise4]{t}[/pale_turquoise4]"


def steel_blue(t: str) -> str:
    """Apply a steel_blue color to text."""

    return f"[steel_blue]{t}[/steel_blue]"


def steel_blue3(t: str) -> str:
    """Apply a steel_blue3 color to text."""

    return f"[steel_blue3]{t}[/steel_blue3]"


def cornflower_blue(t: str) -> str:
    """Apply a cornflower_blue color to text."""

    return f"[cornflower_blue]{t}[/cornflower_blue]"


def dark_sea_green4(t: str) -> str:
    """Apply a dark_sea_green4 color to text."""

    return f"[dark_sea_green4]{t}[/dark_sea_green4]"


def cadet_blue(t: str) -> str:
    """Apply a cadet_blue color to text."""

    return f"[cadet_blue]{t}[/cadet_blue]"


def sky_b1ue3(t: str) -> str:
    """Apply a sky_b1ue3 color to text."""

    return f"[sky_b1ue3]{t}[/sky_b1ue3]"


def chartreuse3(t: str) -> str:
    """Apply a chartreuse3 color to text."""

    return f"[chartreuse3]{t}[/chartreuse3]"


def sea_green3(t: str) -> str:
    """Apply a sea_green3 color to text."""

    return f"[sea_green3]{t}[/sea_green3]"


def aquamarine3(t: str) -> str:
    """Apply a aquamarine3 color to text."""

    return f"[aquamarine3]{t}[/aquamarine3]"


def medium_turquoise(t: str) -> str:
    """Apply a medium_turquoise color to text."""

    return f"[medium_turquoise]{t}[/medium_turquoise]"


def steel_blue1(t: str) -> str:
    """Apply a steel_blue1 color to text."""

    return f"[steel_blue1]{t}[/steel_blue1]"


def sea_green2(t: str) -> str:
    """Apply a sea_green2 color to text."""

    return f"[sea_green2]{t}[/sea_green2]"


def sea_green1(t: str) -> str:
    """Apply a sea_green1 color to text."""

    return f"[sea_green1]{t}[/sea_green1]"


def dark_slate_gray2(t: str) -> str:
    """Apply a dark_slate_gray2 color to text."""

    return f"[dark_slate_gray2]{t}[/dark_slate_gray2]"


def dark_red(t: str) -> str:
    """Apply a dark_red color to text."""

    return f"[dark_red]{t}[/dark_red]"


def dark_magenta(t: str) -> str:
    """Apply a dark_magenta color to text."""

    return f"[dark_magenta]{t}[/dark_magenta]"


def orange4(t: str) -> str:
    """Apply a orange4 color to text."""

    return f"[orange4]{t}[/orange4]"


def light_pink4(t: str) -> str:
    """Apply a light_pink4 color to text."""

    return f"[light_pink4]{t}[/light_pink4]"


def plum4(t: str) -> str:
    """Apply a plum4 color to text."""

    return f"[plum4]{t}[/plum4]"


def medium_purple3(t: str) -> str:
    """Apply a medium_purple3 color to text."""

    return f"[medium_purple3]{t}[/medium_purple3]"


def slate_blue1(t: str) -> str:
    """Apply a slate_blue1 color to text."""

    return f"[slate_blue1]{t}[/slate_blue1]"


def wheat4(t: str) -> str:
    """Apply a wheat4 color to text."""

    return f"[wheat4]{t}[/wheat4]"


def grey53(t: str) -> str:
    """Apply a grey53 color to text."""

    return f"[grey53]{t}[/grey53]"


def light_slate_grey(t: str) -> str:
    """Apply a light_slate_grey color to text."""

    return f"[light_slate_grey]{t}[/light_slate_grey]"


def medium_purple(t: str) -> str:
    """Apply a medium_purple color to text."""

    return f"[medium_purple]{t}[/medium_purple]"


def light_slate_blue(t: str) -> str:
    """Apply a light_slate_blue color to text."""

    return f"[light_slate_blue]{t}[/light_slate_blue]"


def yellow4(t: str) -> str:
    """Apply a yellow4 color to text."""

    return f"[yellow4]{t}[/yellow4]"


def dark_sea_green(t: str) -> str:
    """Apply a dark_sea_green color to text."""

    return f"[dark_sea_green]{t}[/dark_sea_green]"


def light_sky_blue3(t: str) -> str:
    """Apply a light_sky_blue3 color to text."""

    return f"[light_sky_blue3]{t}[/light_sky_blue3]"


def sky_blue2(t: str) -> str:
    """Apply a sky_blue2 color to text."""

    return f"[sky_blue2]{t}[/sky_blue2]"


def chartreuse2(t: str) -> str:
    """Apply a chartreuse2 color to text."""

    return f"[chartreuse2]{t}[/chartreuse2]"


def pale_green3(t: str) -> str:
    """Apply a pale_green3 color to text."""

    return f"[pale_green3]{t}[/pale_green3]"


def dark_slate_gray3(t: str) -> str:
    """Apply a dark_slate_gray3 color to text."""

    return f"[dark_slate_gray3]{t}[/dark_slate_gray3]"


def sky_blue1(t: str) -> str:
    """Apply a sky_blue1 color to text."""

    return f"[sky_blue1]{t}[/sky_blue1]"


def chartreuse1(t: str) -> str:
    """Apply a chartreuse1 color to text."""

    return f"[chartreuse1]{t}[/chartreuse1]"


def light_green(t: str) -> str:
    """Apply a light_green color to text."""

    return f"[light_green]{t}[/light_green]"


def aquamarine1(t: str) -> str:
    """Apply a aquamarine1 color to text."""

    return f"[aquamarine1]{t}[/aquamarine1]"


def dark_slate_gray1(t: str) -> str:
    """Apply a dark_slate_gray1 color to text."""

    return f"[dark_slate_gray1]{t}[/dark_slate_gray1]"


def deep_pink4(t: str) -> str:
    """Apply a deep_pink4 color to text."""

    return f"[deep_pink4]{t}[/deep_pink4]"


def medium_violet_red(t: str) -> str:
    """Apply a medium_violet_red color to text."""

    return f"[medium_violet_red]{t}[/medium_violet_red]"


def dark_violet(t: str) -> str:
    """Apply a dark_violet color to text."""

    return f"[dark_violet]{t}[/dark_violet]"


def purple(t: str) -> str:
    """Apply a purple color to text."""

    return f"[purple]{t}[/purple]"


def medium_orchid3(t: str) -> str:
    """Apply a medium_orchid3 color to text."""

    return f"[medium_orchid3]{t}[/medium_orchid3]"


def medium_orchid(t: str) -> str:
    """Apply a medium_orchid color to text."""

    return f"[medium_orchid]{t}[/medium_orchid]"


def dark_goldenrod(t: str) -> str:
    """Apply a dark_goldenrod color to text."""

    return f"[dark_goldenrod]{t}[/dark_goldenrod]"


def rosy_brown(t: str) -> str:
    """Apply a rosy_brown color to text."""

    return f"[rosy_brown]{t}[/rosy_brown]"


def grey63(t: str) -> str:
    """Apply a grey63 color to text."""

    return f"[grey63]{t}[/grey63]"


def medium_purple2(t: str) -> str:
    """Apply a medium_purple2 color to text."""

    return f"[medium_purple2]{t}[/medium_purple2]"


def medium_purple1(t: str) -> str:
    """Apply a medium_purple1 color to text."""

    return f"[medium_purple1]{t}[/medium_purple1]"


def dark_khaki(t: str) -> str:
    """Apply a dark_khaki color to text."""

    return f"[dark_khaki]{t}[/dark_khaki]"


def navajo_white3(t: str) -> str:
    """Apply a navajo_white3 color to text."""

    return f"[navajo_white3]{t}[/navajo_white3]"


def grey69(t: str) -> str:
    """Apply a grey69 color to text."""

    return f"[grey69]{t}[/grey69]"


def light_steel_blue(t: str) -> str:
    """Apply a light_steel_blue color to text."""

    return f"[light_steel_blue]{t}[/light_steel_blue]"


def dark_olive_green3(t: str) -> str:
    """Apply a dark_olive_green3 color to text."""

    return f"[dark_olive_green3]{t}[/dark_olive_green3]"


def dark_sea_green3(t: str) -> str:
    """Apply a dark_sea_green3 color to text."""

    return f"[dark_sea_green3]{t}[/dark_sea_green3]"


def light_cyan3(t: str) -> str:
    """Apply a light_cyan3 color to text."""

    return f"[light_cyan3]{t}[/light_cyan3]"


def light_sky_blue1(t: str) -> str:
    """Apply a light_sky_blue1 color to text."""

    return f"[light_sky_blue1]{t}[/light_sky_blue1]"


def green_yellow(t: str) -> str:
    """Apply a green_yellow color to text."""

    return f"[green_yellow]{t}[/green_yellow]"


def dark_olive_green2(t: str) -> str:
    """Apply a dark_olive_green2 color to text."""

    return f"[dark_olive_green2]{t}[/dark_olive_green2]"


def pale_green1(t: str) -> str:
    """Apply a pale_green1 color to text."""

    return f"[pale_green1]{t}[/pale_green1]"


def dark_sea_green2(t: str) -> str:
    """Apply a dark_sea_green2 color to text."""

    return f"[dark_sea_green2]{t}[/dark_sea_green2]"


def pale_turquoise1(t: str) -> str:
    """Apply a pale_turquoise1 color to text."""

    return f"[pale_turquoise1]{t}[/pale_turquoise1]"


def red3(t: str) -> str:
    """Apply a red3 color to text."""

    return f"[red3]{t}[/red3]"


def deep_pink3(t: str) -> str:
    """Apply a deep_pink3 color to text."""

    return f"[deep_pink3]{t}[/deep_pink3]"


def magenta3(t: str) -> str:
    """Apply a magenta3 color to text."""

    return f"[magenta3]{t}[/magenta3]"


def dark_orange3(t: str) -> str:
    """Apply a dark_orange3 color to text."""

    return f"[dark_orange3]{t}[/dark_orange3]"


def indian_red(t: str) -> str:
    """Apply a indian_red color to text."""

    return f"[indian_red]{t}[/indian_red]"


def hot_pink3(t: str) -> str:
    """Apply a hot_pink3 color to text."""

    return f"[hot_pink3]{t}[/hot_pink3]"


def hot_pink2(t: str) -> str:
    """Apply a hot_pink2 color to text."""

    return f"[hot_pink2]{t}[/hot_pink2]"


def orchid(t: str) -> str:
    """Apply a orchid color to text."""

    return f"[orchid]{t}[/orchid]"


def orange3(t: str) -> str:
    """Apply a orange3 color to text."""

    return f"[orange3]{t}[/orange3]"


def light_salmon3(t: str) -> str:
    """Apply a light_salmon3 color to text."""

    return f"[light_salmon3]{t}[/light_salmon3]"


def light_pink3(t: str) -> str:
    """Apply a light_pink3 color to text."""

    return f"[light_pink3]{t}[/light_pink3]"


def pink3(t: str) -> str:
    """Apply a pink3 color to text."""

    return f"[pink3]{t}[/pink3]"


def plum3(t: str) -> str:
    """Apply a plum3 color to text."""

    return f"[plum3]{t}[/plum3]"


def violet(t: str) -> str:
    """Apply a violet color to text."""

    return f"[violet]{t}[/violet]"


def gold3(t: str) -> str:
    """Apply a gold3 color to text."""

    return f"[gold3]{t}[/gold3]"


def light_goldenrod3(t: str) -> str:
    """Apply a light_goldenrod3 color to text."""

    return f"[light_goldenrod3]{t}[/light_goldenrod3]"


def tan(t: str) -> str:
    """Apply a tan color to text."""

    return f"[tan]{t}[/tan]"


def misty_rose3(t: str) -> str:
    """Apply a misty_rose3 color to text."""

    return f"[misty_rose3]{t}[/misty_rose3]"


def thistle3(t: str) -> str:
    """Apply a thistle3 color to text."""

    return f"[thistle3]{t}[/thistle3]"


def plum2(t: str) -> str:
    """Apply a plum2 color to text."""

    return f"[plum2]{t}[/plum2]"


def yellow3(t: str) -> str:
    """Apply a yellow3 color to text."""

    return f"[yellow3]{t}[/yellow3]"


def khaki3(t: str) -> str:
    """Apply a khaki3 color to text."""

    return f"[khaki3]{t}[/khaki3]"


def light_yellow3(t: str) -> str:
    """Apply a light_yellow3 color to text."""

    return f"[light_yellow3]{t}[/light_yellow3]"


def grey84(t: str) -> str:
    """Apply a grey84 color to text."""

    return f"[grey84]{t}[/grey84]"


def light_steel_blue1(t: str) -> str:
    """Apply a light_steel_blue1 color to text."""

    return f"[light_steel_blue1]{t}[/light_steel_blue1]"


def yellow2(t: str) -> str:
    """Apply a yellow2 color to text."""

    return f"[yellow2]{t}[/yellow2]"


def dark_olive_green1(t: str) -> str:
    """Apply a dark_olive_green1 color to text."""

    return f"[dark_olive_green1]{t}[/dark_olive_green1]"


def dark_sea_green1(t: str) -> str:
    """Apply a dark_sea_green1 color to text."""

    return f"[dark_sea_green1]{t}[/dark_sea_green1]"


def honeydew2(t: str) -> str:
    """Apply a honeydew2 color to text."""

    return f"[honeydew2]{t}[/honeydew2]"


def light_cyan1(t: str) -> str:
    """Apply a light_cyan1 color to text."""

    return f"[light_cyan1]{t}[/light_cyan1]"


def red1(t: str) -> str:
    """Apply a red1 color to text."""

    return f"[red1]{t}[/red1]"


def deep_pink2(t: str) -> str:
    """Apply a deep_pink2 color to text."""

    return f"[deep_pink2]{t}[/deep_pink2]"


def deep_pink1(t: str) -> str:
    """Apply a deep_pink1 color to text."""

    return f"[deep_pink1]{t}[/deep_pink1]"


def magenta2(t: str) -> str:
    """Apply a magenta2 color to text."""

    return f"[magenta2]{t}[/magenta2]"


def magenta1(t: str) -> str:
    """Apply a magenta1 color to text."""

    return f"[magenta1]{t}[/magenta1]"


def orange_red1(t: str) -> str:
    """Apply a orange_red1 color to text."""

    return f"[orange_red1]{t}[/orange_red1]"


def indian_red1(t: str) -> str:
    """Apply a indian_red1 color to text."""

    return f"[indian_red1]{t}[/indian_red1]"


def hot_pink(t: str) -> str:
    """Apply a hot_pink color to text."""

    return f"[hot_pink]{t}[/hot_pink]"


def medium_orchid1(t: str) -> str:
    """Apply a medium_orchid1 color to text."""

    return f"[medium_orchid1]{t}[/medium_orchid1]"


def dark_orange(t: str) -> str:
    """Apply a dark_orange color to text."""

    return f"[dark_orange]{t}[/dark_orange]"


def salmon1(t: str) -> str:
    """Apply a salmon1 color to text."""

    return f"[salmon1]{t}[/salmon1]"


def light_coral(t: str) -> str:
    """Apply a light_coral color to text."""

    return f"[light_coral]{t}[/light_coral]"


def pale_violet_red1(t: str) -> str:
    """Apply a pale_violet_red1 color to text."""

    return f"[pale_violet_red1]{t}[/pale_violet_red1]"


def orchid2(t: str) -> str:
    """Apply a orchid2 color to text."""

    return f"[orchid2]{t}[/orchid2]"


def orchid1(t: str) -> str:
    """Apply a orchid1 color to text."""

    return f"[orchid1]{t}[/orchid1]"


def orange1(t: str) -> str:
    """Apply a orange1 color to text."""

    return f"[orange1]{t}[/orange1]"


def sandy_brown(t: str) -> str:
    """Apply a sandy_brown color to text."""

    return f"[sandy_brown]{t}[/sandy_brown]"


def light_salmon1(t: str) -> str:
    """Apply a light_salmon1 color to text."""

    return f"[light_salmon1]{t}[/light_salmon1]"


def light_pink1(t: str) -> str:
    """Apply a light_pink1 color to text."""

    return f"[light_pink1]{t}[/light_pink1]"


def pink1(t: str) -> str:
    """Apply a pink1 color to text."""

    return f"[pink1]{t}[/pink1]"


def plum1(t: str) -> str:
    """Apply a plum1 color to text."""

    return f"[plum1]{t}[/plum1]"


def gold1(t: str) -> str:
    """Apply a gold1 color to text."""

    return f"[gold1]{t}[/gold1]"


def light_goldenrod2(t: str) -> str:
    """Apply a light_goldenrod2 color to text."""

    return f"[light_goldenrod2]{t}[/light_goldenrod2]"


def navajo_white1(t: str) -> str:
    """Apply a navajo_white1 color to text."""

    return f"[navajo_white1]{t}[/navajo_white1]"


def misty_rosel(t: str) -> str:
    """Apply a misty_rosel color to text."""

    return f"[misty_rosel]{t}[/misty_rosel]"


def thistle1(t: str) -> str:
    """Apply a thistle1 color to text."""

    return f"[thistle1]{t}[/thistle1]"


def yellow1(t: str) -> str:
    """Apply a yellow1 color to text."""

    return f"[yellow1]{t}[/yellow1]"


def light_goldenrod1(t: str) -> str:
    """Apply a light_goldenrod1 color to text."""

    return f"[light_goldenrod1]{t}[/light_goldenrod1]"


def khaki1(t: str) -> str:
    """Apply a khaki1 color to text."""

    return f"[khaki1]{t}[/khaki1]"


def wheat1(t: str) -> str:
    """Apply a wheat1 color to text."""

    return f"[wheat1]{t}[/wheat1]"


def cornsilk1(t: str) -> str:
    """Apply a cornsilk1 color to text."""

    return f"[cornsilk1]{t}[/cornsilk1]"


def grey100(t: str) -> str:
    """Apply a grey100 color to text."""

    return f"[grey100]{t}[/grey100]"


def grey3(t: str) -> str:
    """Apply a grey3 color to text."""

    return f"[grey3]{t}[/grey3]"


def grey7(t: str) -> str:
    """Apply a grey7 color to text."""

    return f"[grey7]{t}[/grey7]"


def grey11(t: str) -> str:
    """Apply a grey11 color to text."""

    return f"[grey11]{t}[/grey11]"


def grey15(t: str) -> str:
    """Apply a grey15 color to text."""

    return f"[grey15]{t}[/grey15]"


def grey19(t: str) -> str:
    """Apply a grey19 color to text."""

    return f"[grey19]{t}[/grey19]"


def grey23(t: str) -> str:
    """Apply a grey23 color to text."""

    return f"[grey23]{t}[/grey23]"


def grey27(t: str) -> str:
    """Apply a grey27 color to text."""

    return f"[grey27]{t}[/grey27]"


def grey30(t: str) -> str:
    """Apply a grey30 color to text."""

    return f"[grey30]{t}[/grey30]"


def grey35(t: str) -> str:
    """Apply a grey35 color to text."""

    return f"[grey35]{t}[/grey35]"


def grey39(t: str) -> str:
    """Apply a grey39 color to text."""

    return f"[grey39]{t}[/grey39]"


def grey42(t: str) -> str:
    """Apply a grey42 color to text."""

    return f"[grey42]{t}[/grey42]"


def grey46(t: str) -> str:
    """Apply a grey46 color to text."""

    return f"[grey46]{t}[/grey46]"


def grey59(t: str) -> str:
    """Apply a grey59 color to text."""

    return f"[grey59]{t}[/grey59]"


def grey54(t: str) -> str:
    """Apply a grey54 color to text."""

    return f"[grey54]{t}[/grey54]"


def grey58(t: str) -> str:
    """Apply a grey58 color to text."""

    return f"[grey58]{t}[/grey58]"


def grey62(t: str) -> str:
    """Apply a grey62 color to text."""

    return f"[grey62]{t}[/grey62]"


def grey66(t: str) -> str:
    """Apply a grey66 color to text."""

    return f"[grey66]{t}[/grey66]"


def grey70(t: str) -> str:
    """Apply a grey70 color to text."""

    return f"[grey70]{t}[/grey70]"


def grey74(t: str) -> str:
    """Apply a grey74 color to text."""

    return f"[grey74]{t}[/grey74]"


def grey78(t: str) -> str:
    """Apply a grey78 color to text."""

    return f"[grey78]{t}[/grey78]"


def grey82(t: str) -> str:
    """Apply a grey82 color to text."""

    return f"[grey82]{t}[/grey82]"


def grey85(t: str) -> str:
    """Apply a grey85 color to text."""

    return f"[grey85]{t}[/grey85]"


def grey89(t: str) -> str:
    """Apply a grey89 color to text."""

    return f"[grey89]{t}[/grey89]"


def grey93(t: str) -> str:
    """Apply a grey93 color to text."""

    return f"[grey93]{t}[/grey93]"
