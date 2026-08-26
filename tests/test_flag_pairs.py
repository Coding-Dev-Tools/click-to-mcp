"""Flag-pair and option-spelling handling in the adapter handler."""
import click

from click_to_mcp.adapter import _build_click_tool_def


@click.command()
@click.option("--color/--no-color", default=True, help="Use color")
def pair(color: bool) -> None:
    click.echo(f"color={color}")


@click.command()
@click.option("-n", "num", type=int, help="Short-only option")
def shortonly(num: int) -> None:
    click.echo(f"num={num}")


def test_flag_pair_false_emits_negative() -> None:
    tool = _build_click_tool_def(pair)
    # Default is True, so False output proves --no-color was passed.
    assert "color=False" in tool.handler(color=False)


def test_flag_pair_true_emits_positive() -> None:
    tool = _build_click_tool_def(pair)
    assert "color=True" in tool.handler(color=True)


def test_short_only_option_uses_real_spelling() -> None:
    tool = _build_click_tool_def(shortonly)
    # Must invoke "-n", not an invented "--num".
    out = tool.handler(num=5)
    assert "num=5" in out


def test_plain_flag_false_is_dropped() -> None:
    @click.command()
    @click.option("--verbose", is_flag=True, default=False)
    def cmd(verbose: bool) -> None:
        click.echo(f"verbose={verbose}")

    tool = _build_click_tool_def(cmd)
    assert "verbose=False" in tool.handler()
