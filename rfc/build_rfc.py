#!/usr/bin/env python3
##
## EPITECH PROJECT, 2026
## Project - Documentation
## File description:
## Builds docs/rfc-rtype.txt, the protocol
## in the classic RFC text format
##

"""Builds the R-Type protocol RFC as a classic RFC text document.

The format follows RFC 7322 (RFC Style Guide): plain ASCII, at most
72 characters per line, pages of 58 lines with a running header and
footer, separated by form feeds, and a table of contents with page
numbers. Packet layouts are drawn as 32-bit rulers, like in IETF RFCs.

Usage: python3 rfc/build_rfc.py  (writes docs/rfc-rtype.txt)
"""

import os
import textwrap

RFC_NUMBER = "9999"
TITLE = "R-Type Game Protocol"
SHORT_TITLE = "R-Type Protocol"
DATE = "November 2026"
AUTHOR = "Space-Type"
CATEGORY = "Informational"

WIDTH = 72
PAGE_LINES = 58
INDENT = "   "

OUTPUT = os.path.join(os.path.dirname(__file__), "..", "docs", "rfc-rtype.txt")


# --------------------------------------------------------------------- #
#  Blocks: a document is a list of blocks, each a list of lines          #
# --------------------------------------------------------------------- #

class Block:
    """Lines that are kept together on a page when `keep` is set."""

    def __init__(self, lines, keep=False, heading=None):
        self.lines = lines
        self.keep = keep
        self.heading = heading  # (number, title) for the table of contents


def para(text, indent=INDENT):
    text = " ".join(text.split())
    return Block(textwrap.wrap(text, WIDTH, initial_indent=indent, subsequent_indent=indent,
                               break_on_hyphens=False) + [""])


def bullets(items, indent=INDENT):
    lines = []
    for item in items:
        item = " ".join(item.split())
        lines += textwrap.wrap(item, WIDTH, initial_indent=indent + "o  ",
                               subsequent_indent=indent + "   ", break_on_hyphens=False)
        lines.append("")
    return Block(lines)


def numbered(items, indent=INDENT):
    lines = []
    for number, item in enumerate(items, 1):
        item = " ".join(item.split())
        prefix = f"{number}.  "
        lines += textwrap.wrap(item, WIDTH, initial_indent=indent + prefix,
                               subsequent_indent=indent + " " * len(prefix), break_on_hyphens=False)
        lines.append("")
    return Block(lines)


def figure(text, indent=INDENT, title=None):
    lines = [indent + line if line else "" for line in textwrap.dedent(text).strip("\n").split("\n")]
    for line in lines:
        assert len(line) <= WIDTH, f"figure line too long ({len(line)}): {line}"
    lines.append("")
    if title:
        lines += [title.center(WIDTH).rstrip(), ""]
    return Block(lines, keep=True)


def table(header, rows, indent=INDENT):
    """A plain text table; the last column wraps."""
    widths = [max(len(str(row[i])) for row in [header] + rows) for i in range(len(header) - 1)]
    last = WIDTH - len(indent) - sum(w + 2 for w in widths)
    assert last >= 20, "table too wide"

    def render(row):
        wrapped = textwrap.wrap(str(row[-1]), last) or [""]
        out = []
        for n, piece in enumerate(wrapped):
            cells = [(str(row[i]) if n == 0 else "").ljust(widths[i]) for i in range(len(widths))]
            out.append((indent + "  ".join(cells) + "  " + piece).rstrip())
        return out

    lines = render(header)
    lines.append((indent + "  ".join("-" * w for w in widths) + "  " + "-" * min(last, max(len(header[-1]), 10))).rstrip())
    for row in rows:
        lines += render(row)
    lines.append("")
    return Block(lines, keep=len(lines) < 30)


def heading(number, title):
    return Block([f"{number}.  {title}", ""], heading=(number, title))


def packet(fields, variable=None):
    """A 32-bit ruler diagram; fields are (name, bytes), packed from byte 0.

    `variable` names a variable-length part that ends the packet.
    """
    ruler = ["    0                   1                   2                   3",
             "    0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1"]
    full = "   +" + "-+" * 32
    rows = []              # each row: list of (label, bytes)
    used = 0               # bytes used in the current row
    for name, size in fields:
        first = True
        while size > 0:
            if used == 0:
                rows.append([])
            take = min(4 - used, size)
            rows[-1].append((name if first else f"{name} (cont.)", take))
            used = (used + take) % 4
            size -= take
            first = False
    if variable:
        if used == 0:
            rows.append([])
        rows[-1].append((f"{variable} ...", 4 - used if used else 4))
        used = 0

    lines = ruler + [full]
    for row in rows:
        cells = []
        for label, size in row:
            width = size * 16 - 1
            if len(label) > width:
                label = label.replace(" (cont.)", "")[:width]
            cells.append(label.center(width))
        lines.append("   |" + "|".join(cells) + "|")
        span = sum(size for _, size in row)
        lines.append(full if span == 4 else "   +" + "-+" * (span * 8))
    lines.append("")
    for line in lines:
        assert len(line) <= WIDTH, f"diagram line too long: {line}"
    return Block(lines, keep=True)


# --------------------------------------------------------------------- #
#  Pagination                                                            #
# --------------------------------------------------------------------- #

def header_line(page):
    left, center, right = f"RFC {RFC_NUMBER}", SHORT_TITLE, DATE
    gap = WIDTH - len(left) - len(right)
    middle = center.center(gap)
    return left + middle + right


def footer_line(page):
    left, center, right = AUTHOR, CATEGORY, f"[Page {page}]"
    gap = WIDTH - len(left) - len(right)
    return left + center.center(gap) + right


def paginate(blocks, first_page_lines):
    """Returns (pages, headings with their page)."""
    pages = [[]]
    found = []

    def capacity():
        # page 1: the front matter instead of the running header; then 2 blank lines and the footer
        return PAGE_LINES - 3 - len(first_page_lines) if len(pages) == 1 else PAGE_LINES - 6

    # A heading stays on the same page as the indivisible block right after it
    merged = []
    for block in blocks:
        if merged and merged[-1].heading and not merged[-1].keep and block.keep and len(merged[-1].lines) <= 2:
            merged[-1] = Block(merged[-1].lines + block.lines, keep=True, heading=merged[-1].heading)
        else:
            merged.append(block)

    for block in merged:
        lines = block.lines
        current = pages[-1]
        body_lines = capacity()
        # A heading stays with the start of what follows it (handled by the caller merging)
        if block.keep and len(lines) <= body_lines and len(current) + len(lines) > body_lines:
            pages.append([])
            current = pages[-1]
        if block.heading:
            if len(current) + 4 > body_lines:
                pages.append([])
                current = pages[-1]
            found.append((block.heading, len(pages)))
        for line in lines:
            if len(current) >= capacity():
                pages.append([])
                current = pages[-1]
                if line == "":
                    continue
            current.append(line)
    # Trailing blank lines of a page are not needed
    return pages, found


def render(pages, first_page_lines):
    out = []
    for number, lines in enumerate(pages, 1):
        if number == 1:
            page = first_page_lines + lines
        else:
            page = [header_line(number), "", ""] + lines
        while page and page[-1] == "":
            page.pop()
        page += [""] * (PAGE_LINES - 1 - len(page))
        assert len(page) <= PAGE_LINES - 1, f"page {number} overflows"
        page.append(footer_line(number))
        out.append("\n".join(line.rstrip() for line in page))
    return "\n\f\n".join(out) + "\n"


# --------------------------------------------------------------------- #
#  Content                                                               #
# --------------------------------------------------------------------- #

def front_matter():
    left = ["Space-Type Working Group",
            f"Request for Comments: {RFC_NUMBER}",
            f"Category: {CATEGORY}"]
    right = [AUTHOR, "Epitech", DATE]
    lines = []
    for l, r in zip(left, right):
        lines.append(l + " " * (WIDTH - len(l) - len(r)) + r)
    lines += ["", "", TITLE.center(WIDTH).rstrip(), ""]
    return lines


def abstract_blocks():
    return [
        Block(["Abstract", ""]),
        para("""This document specifies the binary protocol spoken over UDP
        between the R-Type game server and its clients, as implemented by
        the Space-Type project. It describes the transport, the encoding of
        every packet and shared component, the life cycle of a player
        session, how the game stays consistent over a lossy network, and
        the checks a peer must make on what it receives. It is meant to be
        complete enough to write a new client without reading the reference
        implementation."""),
        Block(["Status of This Memo", ""]),
        para("""This document is not an Internet Standards Track
        specification, and it is not a product of the IETF. It is published
        for informational purposes by the Space-Type team, as the protocol
        documentation of its R-Type project (Epitech, B-CPP-500). Its RFC
        number is internal to the project."""),
        para("""The reference implementation is the Protecs library, used by
        r-type_server and r-type_client
        (https://github.com/Space-Type)."""),
        Block(["Copyright Notice", ""]),
        para("""Copyright (c) 2026 the Space-Type team. This document may be
        copied and distributed freely, in full and unmodified."""),
    ]


def toc_block(found, pages_of_toc):
    lines = ["Table of Contents", ""]
    for (number, title), page in found:
        depth = number.count(".")
        label = INDENT + "  " * depth + (f"{number}.  {title} " if number else f"{title} ")
        dots = "." * max(2, WIDTH - len(label) - len(str(page)) - 1)
        lines.append(f"{label}{dots} {page}")
    lines.append("")
    return lines


def body():
    b = []
    S = lambda n, t: b.append(heading(n, t))
    P = lambda t: b.append(para(t))

    S("1", "Introduction")
    P("""R-Type is a networked horizontal shoot'em up for up to four
    players. A server runs the game and has the final word on everything
    that happens in it: positions, shots, hits, scores, lives and stages.
    Clients only send the inputs of their player, and display the game as
    the server describes it.""")
    P("""The game state is a set of entities (players, enemies, missiles,
    the level). Each entity has components (position, health, score...).
    The server replicates the shared components of every entity to every
    client. Both sides run the simulation at a fixed rate of 120 ticks per
    second, and most packets carry the simulation tick they apply to.""")

    S("1.1", "Requirements Language")
    P("""The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL
    NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY",
    and "OPTIONAL" in this document are to be interpreted as described in
    BCP 14 [RFC2119] [RFC8174] when, and only when, they appear in all
    capitals, as shown here.""")

    S("1.2", "Terminology")
    b.append(table(["Term", "Meaning"], [
        ["Server", "The r-type_server program, authoritative on the game."],
        ["Client", "A program that joined a game on behalf of one player."],
        ["Tick", "One step of the simulation; 120 ticks per second."],
        ["Entity", "Anything in the game, identified by a network id."],
        ["Component", "A piece of data of an entity, replicated by the server."],
        ["Datagram", "One UDP datagram; it carries exactly one packet."],
    ]))

    S("2", "Transport")
    b.append(bullets([
        """All communication uses UDP [RFC768]. There is no TCP
        connection: a lost or late game update is worthless once the next
        one is sent, and UDP lets the game go on without waiting for
        retransmissions.""",
        """The server listens on UDP port 5432, on every interface. A client
        uses any local port; the server answers to the address and port a
        datagram came from.""",
        """One datagram carries exactly one packet.""",
        """A datagram MUST NOT be longer than 64 bytes. Receivers read at
        most 64 bytes per datagram; a longer one is truncated, and then
        usually rejected as malformed.""",
        """UDP does not guarantee delivery, order or uniqueness. A peer MUST
        NOT assume that a packet arrives, arrives once, or arrives in order.
        Section 7.3 explains how the protocol copes with it.""",
    ]))

    S("3", "Data Types")
    P("""All multi-byte values are little-endian. A peer running on a
    big-endian machine MUST swap the bytes. Fields are packed: there is no
    padding between them, and a packet is exactly as long as its fields.""")
    b.append(table(["Type", "Size", "Encoding"], [
        ["u8", "1", "Unsigned integer."],
        ["u16", "2", "Unsigned integer, little-endian."],
        ["u32", "4", "Unsigned integer, little-endian."],
        ["u64", "8", "Unsigned integer, little-endian."],
        ["i64", "8", "Signed integer (two's complement), little-endian."],
        ["f32", "4", "IEEE 754 single precision float, little-endian."],
        ["bool", "1", "0 is false, any other value is true."],
        ["bits64", "8", "64 flags: flag i is bit (i mod 8), least significant first, of byte (i div 8)."],
        ["str32", "1-33", "A u8 length (0 to 32), then that many bytes of text, no terminator."],
    ]))
    P("""In the packets below, "Tick" is a u32 simulation tick, and "Id" is
    a u64 network entity id (Section 6.1).""")

    S("4", "Packet Format")
    P("""Every packet starts with a one-byte type, followed by a payload
    whose layout depends on the type.""")
    b.append(figure("""
         0                   1                   2                   3
         0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |     Type      |     Payload (0 to 63 bytes, depends on Type) ...
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    """, title="Figure 1: Packet Format"))
    b.append(table(["Type", "Name", "Direction", "Size"], [
        ["0", "EntityComponentData", "S->C", "15 + component"],
        ["1", "EntityCreate", "S->C", "14"],
        ["2", "EntityDelete", "S->C", "13"],
        ["3", "EntityList", "both", "9 + 16 per entity"],
        ["4", "EntityRemoveComponent", "S->C", "15"],
        ["5", "EntitySyncComponents", "both", "21"],
        ["6", "Ping", "both", "1"],
        ["7", "PlayerId", "both", "9"],
        ["8", "PlayerInput", "both", "8"],
        ["9", "PlayerJoin", "C->S", "2 to 34"],
        ["10", "PlayerLeave", "both", "1"],
        ["11", "TickSync", "both", "25"],
    ]))
    P("""Sizes include the type byte. A receiver MUST drop a packet of an
    unknown type (12 or more).""")

    S("5", "Packets")
    S("5.1", "EntityComponentData (Type 0)")
    P("""The value of one shared component of an entity. The server sends
    one for every shared component of every entity, 20 times per
    second.""")
    b.append(packet([("Type = 0", 1), ("Tick", 4), ("Id", 8), ("Component", 2)], variable="Data"))
    b.append(bullets([
        "Component: u16 component type (Section 6.3).",
        "Data: the component value, as defined in Section 6.3.",
    ]))
    P("""A receiver that does not know the entity SHOULD ask for the entity
    list (Section 7.3) and drop the packet.""")

    S("5.2", "EntityCreate (Type 1)")
    b.append(packet([("Type = 1", 1), ("Tick", 4), ("Id", 8), ("Kind", 1)]))
    P("""Kind is a u8 entity kind (Section 6.2): what to draw. The
    components of the new entity follow as EntityComponentData
    packets.""")

    S("5.3", "EntityDelete (Type 2)")
    b.append(packet([("Type = 2", 1), ("Tick", 4), ("Id", 8)]))
    P("""The receiver removes the entity and its components. Tick 0 means
    "now". A client SHOULD show the death of an enemy or a player (an
    explosion) when its entity is deleted.""")

    S("5.4", "EntityList (Type 3)")
    b.append(packet([("Type = 3", 1), ("Tick", 4), ("Count", 4)], variable="Entries"))
    P("""Count is a u32. Each of the Count entries is 16 bytes: the Id of an
    entity (u64), then the set of its shared components (bits64, flag i
    set when it has component type i).""")
    b.append(bullets([
        """Client to server: a request for the list, sent with Count = 0.""",
        """Server to client: the list of every entity. 64 bytes hold 3
        entries, so the server sends as many EntityList packets as needed,
        each with at most 3 entries. A receiver MUST handle each packet on
        its own, and MUST NOT expect them all to arrive.""",
        """A receiver MUST reject a packet whose Count needs more bytes than
        the datagram holds.""",
    ]))

    S("5.5", "EntityRemoveComponent (Type 4)")
    b.append(packet([("Type = 4", 1), ("Tick", 4), ("Id", 8), ("Component", 2)]))
    P("""The receiver removes the component (u16 type) from the entity.""")

    S("5.6", "EntitySyncComponents (Type 5)")
    b.append(packet([("Type = 5", 1), ("Tick", 4), ("Id", 8), ("Components", 8)]))
    b.append(bullets([
        """Client to server: "this is the set of shared components I have
        for this entity" (bits64).""",
        """Server to client: the server's own set, followed by an
        EntityComponentData for each component the client lacks, and an
        EntityRemoveComponent for each one it should not have.""",
    ]))

    S("5.7", "Ping (Type 6)")
    b.append(packet([("Type = 6", 1)]))
    P("""No payload. The server sends one to every player every second, and
    a client MUST answer it with a Ping. A player the server has heard
    nothing from for 15 seconds is considered gone (Section 7.1).""")

    S("5.8", "PlayerId (Type 7)")
    b.append(packet([("Type = 7", 1), ("Id", 8)]))
    b.append(bullets([
        """Server to client: the answer to a join, with the id of the
        player's own entity. Id 0 means that the server refused the
        player.""",
        """Client to server: "I lost my id". The server sends the PlayerId
        again. The Id sent by the client is ignored and SHOULD be 0. The
        server ignores it from an address that did not join.""",
    ]))

    S("5.9", "PlayerInput (Type 8)")
    b.append(packet([("Type = 8", 1), ("Tick", 4), ("Sequence", 1), ("Input", 1), ("State", 1)]))
    b.append(table(["Field", "Meaning"], [
        ["Tick", "Tick the input applies to, in the server's time (Section 7.2)."],
        ["Sequence", "u8 order of the inputs sent for the same tick."],
        ["Input", "0 up, 1 down, 2 left, 3 right, 4 fire."],
        ["State", "0 pressed (held down), 1 released."],
    ]))
    b.append(bullets([
        """Client to server: a change of one input of the player.""",
        """Server to client: a request for the full input state, sent every
        0.5 seconds with all fields 0. The client answers with five
        PlayerInput packets for the same tick, Sequence 0 to 4, one per
        input (up, down, left, right, fire), with the state it holds now.
        A lost press or release is thus corrected within half a
        second.""",
    ]))
    P("""The server ignores an input for a tick it already simulated.
    Holding fire charges the shot; releasing it fires (Section 6.4).""")

    S("5.10", "PlayerJoin (Type 9)")
    b.append(packet([("Type = 9", 1), ("Length", 1)], variable="Name"))
    P("""Name is a str32: the player's name, Length bytes long. A Length
    over 32 MUST be rejected. It is the first packet of a client (Section
    7.1). The server ignores a PlayerJoin from an address that already
    joined.""")

    S("5.11", "PlayerLeave (Type 10)")
    b.append(packet([("Type = 10", 1)]))
    b.append(bullets([
        """Client to server: the player quits. The server deletes its
        entity and sends EntityDelete to the other clients.""",
        """Server to client: the client was removed from the game and
        SHOULD end its session.""",
    ]))

    S("5.12", "TickSync (Type 11)")
    b.append(packet([("Type = 11", 1), ("Client Tick", 4), ("Server Tick", 4),
                     ("Client Time", 8), ("Server Time", 8)]))
    b.append(table(["Field", "Meaning"], [
        ["Client Tick", "u32: client's tick when it sent the request."],
        ["Server Tick", "u32: server's tick when it answered (0 in a request)."],
        ["Client Time", "i64: client's clock when it sent the request, opaque to the server."],
        ["Server Time", "i64: server's monotonic clock, in nanoseconds, when it answered."],
    ]))
    P("""The client sends it with its own values, and the server sends it
    back with Client Tick and Client Time unchanged (Section 7.2). The
    server also sends one right after a join.""")

    S("6", "Game Data")
    S("6.1", "Entities and Ids")
    b.append(bullets([
        """Entity ids are chosen by the server. A client MUST treat them as
        opaque u64 values, and MUST NOT assume that they are small or
        consecutive. The reference server mixes a time stamp in the upper
        32 bits, so an id is not reused when an entity slot is.""",
        """The value 0 is never a valid entity; PlayerId uses it for
        "refused".""",
    ]))

    S("6.2", "Entity Kinds")
    b.append(table(["Kind", "Name", "Meaning"], [
        ["0", "GENERIC", "Nothing to draw. The level is such an entity (component Level)."],
        ["1", "PLAYER", "A player's ship, coloured by PlayerStats.Slot."],
        ["2", "ENEMY_PATA_PATA", "Small enemy flying in waves."],
        ["3", "ENEMY_SCANT", "Enemy."],
        ["4", "PLAYER_MISSILE", "Missile shot by a player."],
        ["5", "ENEMY_MISSILE", "Missile shot by an enemy or a boss."],
        ["6-10", "PLAYER_BEAM_1-5", "Charged beam of a player, by charge level."],
        ["11", "ENEMY_DOBKERATOPS", "Stage 1 boss body: armored, takes no damage."],
        ["12", "DOBKERATOPS_CORE", "Stage 1 boss weak point: its Health is the boss health, its deletion is the boss death."],
    ]))
    P("""New kinds are added at the end: existing values never change. A
    client SHOULD draw an unknown kind as a generic object rather than
    drop it.""")

    S("6.3", "Components")
    P("""The world is 800 x 450 units; x grows to the right and y
    downwards. A component type is the index of the component in this
    table. New components are added at the end: existing types never
    change. The server sends every component of every entity 20 times per
    second, except PlayerInput.""")
    b.append(table(["Type", "Component", "Size", "Fields"], [
        ["0", "Level", "6", "Progression u32 (pixels of the stage background scrolled), Stage u8 (1 to 8), Won bool (the last stage is cleared: the game is won)."],
        ["1", "Movement", "12", "Direction 2 x f32, Speed f32."],
        ["2", "PathFinding", "13", "Type u8 (0 straight), Target Velocity 2 x f32, Acceleration f32."],
        ["3", "PlayerInput", "1", "u8 flags: bit 4 up, bit 3 down, bit 2 left, bit 1 right, bit 0 fire."],
        ["4", "PlayerStats", "7", "Slot u8 (0 to 3, the player's colour), Lives u8 (0: out of the game), Score u32, Charge u8 (0 to 5, while fire is held)."],
        ["5", "Transform", "16", "Position 2 x f32 (top-left corner), Rotation f32, Scale f32 (draw the sprite that much bigger)."],
        ["6", "Velocity", "12", "Position 2 x f32 (units per tick), Angular f32."],
        ["7", "PlayerName", "1-33", "str32: the player's name."],
        ["8", "Health", "4", "HP u16, Max u16."],
    ]))

    S("6.4", "Gameplay Shown by Clients")
    b.append(bullets([
        """Players: PlayerStats.Lives hearts, the score, and the charge
        level while the player charges. At Lives = 0 the player is out,
        and the others play on.""",
        """Charged shot: tap fire for a missile; hold it to charge (one
        level per 0.4 seconds, up to 5); release it to fire a beam
        (PLAYER_BEAM_n).""",
        """Level: one GENERIC entity with a Level component. A change of
        Stage starts a new stage; Won = true ends the game with a
        victory.""",
        """Boss: the Health of the DOBKERATOPS_CORE entity is the boss
        health.""",
    ]))

    S("7", "Protocol Behavior")
    S("7.1", "Session Life Cycle")
    b.append(figure("""
        Client                         Server                Other clients
          |                              |                         |
          |---- PlayerJoin(name) ------->|                         |
          |                              | (no answer after 1 s:   |
          |                              |  PlayerJoin + PlayerId  |
          |                              |  again, give up at 5 s) |
          |<--- PlayerId(id) ------------|                         |
          |<--- TickSync ----------------|                         |
          |<--- EntityCreate(PLAYER) ----|---- EntityCreate ------>|
          |<--- EntityList x n ----------|                         |
          |                              |                         |
          |<--- EntityComponentData -----|---- (20 per second) --->|
          |<--- Ping (every second) -----|                         |
          |---- Ping ------------------->|                         |
          |---- PlayerInput (changes) -->|                         |
          |                              |                         |
          |---- PlayerLeave ------------>|                         |
          |   (or 15 s of silence)       |---- EntityDelete(id) -->|
    """, title="Figure 2: Session Life Cycle"))
    b.append(numbered([
        """The client sends PlayerJoin. Without an answer within a second,
        it sends PlayerJoin again with a PlayerId (in case the server's
        answer was lost), and gives up after 5 seconds.""",
        """The server registers the address, answers PlayerId and TickSync,
        announces the new player to everyone (EntityCreate), and sends the
        entity list. The first player to join starts the level; when the
        last player leaves, the server deletes every entity, and the level
        starts over with the next player.""",
        """To quit, the client sends PlayerLeave.""",
        """If a client crashes or loses its connection, it stops answering.
        The server removes a player it has received nothing from for 15
        seconds, exactly as if it had sent PlayerLeave: the other clients
        get its EntityDelete, and the game goes on.""",
    ]))

    S("7.2", "Ticks and Clock Synchronization")
    b.append(bullets([
        """Both sides count ticks at 120 per second, from their own start.
        The difference between the server's tick and the client's is
        measured with TickSync: the client sends one about every 100 ticks;
        with the answer, the round trip time is (now - Client Time), and
        the server's current tick is about Server Tick + (round trip / 2) x
        120.""",
        """A client MUST stamp its PlayerInput with a tick in the server's
        time, slightly ahead of it, so that the input reaches the server
        before that tick is simulated.""",
        """A receiver queues the packets that have a tick, and applies them
        when its simulation reaches that tick. Packets without a tick, and
        packets with tick 0, are applied at once.""",
    ]))

    S("7.3", "Consistency over a Lossy Network")
    P("""UDP may lose any packet. The protocol never retransmits; it repeats
    state instead:""")
    b.append(bullets([
        """Component values are sent 20 times per second: a lost value is
        replaced 50 ms later.""",
        """Inputs are re-sent in full every 0.5 seconds, on the server's
        request (Section 5.9).""",
        """A lost EntityCreate: the client receives data for an entity it
        does not know, and asks for the entity list (EntityList with Count
        = 0). For an entity whose components differ, it sends
        EntitySyncComponents, and the server answers with the missing or
        extra components.""",
        """A lost EntityDelete: a client SHOULD forget an entity the server
        has not updated for one second while other updates keep arriving
        (the server updates every entity 20 times per second). With 20 %
        of the datagrams lost, this removes about 92 % of the entities that
        would otherwise stay on screen after their deletion (measured with
        the project's benchmarks).""",
    ]))
    P("""There are no sequence numbers, acknowledgements or retransmissions:
    everything the server sends is either repeated anyway or can be
    recovered on demand, and a retransmitted packet would arrive later than
    the next repetition. Events that must not be missed are deduced from the
    state: a death is the deletion of an entity, a lost life is a smaller
    PlayerStats.Lives, a victory is Level.Won.""")

    S("7.4", "Example Exchange")
    P("""Alice joins, the server gives her the id 0x1a2b3c4d00000007, she
    holds fire, and an enemy dies. Bytes in hexadecimal, as sent on the
    wire:""")
    b.append(figure("""
        C->S  PlayerJoin("alice")
              09 05 61 6c 69 63 65

        S->C  PlayerId(0x1a2b3c4d00000007)
              07 07 00 00 00 4d 3c 2b 1a

        S->C  EntityComponentData, tick 1000, her Transform:
              position (123.5, 67.25), rotation 0, scale 1
              00 e8 03 00 00 07 00 00 00 4d 3c 2b 1a 05 00
              00 00 f7 42 00 80 86 42 00 00 00 00 00 00 80 3f

        C->S  PlayerInput, tick 1012, sequence 0, fire, pressed
              08 f4 03 00 00 00 04 00

        S->C  EntityDelete, tick 0 (now), entity 0x1a2b3c4d00000009
              02 00 00 00 00 09 00 00 00 4d 3c 2b 1a
    """, title="Figure 3: Example Exchange"))

    S("8", "Security Considerations")
    P("""A peer receives datagrams from anyone. Before using a packet, a
    receiver MUST:""")
    b.append(numbered([
        "Reject an empty datagram, and read at most 64 bytes.",
        "Reject an unknown packet type (12 or more).",
        """Check that the datagram holds the fixed fields of the type
        before reading them, then that it holds every variable part:
        str32 lengths (at most 32) and the EntityList Count (16 bytes per
        entry).""",
        "Reject an unknown component type (9 or more) in EntityComponentData.",
        """Treat a packet that fails a check as if it never arrived: drop
        it, keep running, and keep no state about it.""",
    ]))
    P("""The server MUST also:""")
    b.append(bullets([
        """Ignore every packet but PlayerJoin from an address that did not
        join.""",
        """Ignore inputs for ticks already simulated, and keep a bounded
        number of pending inputs per player (the reference server keeps
        50).""",
        """Never trust a client for anything but its inputs: positions,
        hits, scores and deaths are computed by the server.""",
    ]))
    P("""Clients only send inputs. Positions, hits, scores and deaths are
    computed by the server, so a forged or replayed packet cannot change
    them.""")
    P("""The reference server was tested with 100 000 malformed datagrams of
    five kinds (random bytes, random payload of a known type, an EntityList
    announcing 4 billion entries, a PlayerJoin with a 255-byte name, an
    unknown component type): it did not crash, and still accepted a new
    player in under a millisecond.""")

    S("9", "IANA Considerations")
    P("""This document has no IANA actions. Port 5432 is the default port
    of the reference implementation; it is not registered for this
    protocol, and a deployment MAY use another port.""")

    S("10", "References")
    S("10.1", "Normative References")
    b.append(table(["Reference", "Document"], [
        ["[RFC768]", "Postel, J., \"User Datagram Protocol\", STD 6, RFC 768, August 1980."],
        ["[RFC2119]", "Bradner, S., \"Key words for use in RFCs to Indicate Requirement Levels\", BCP 14, RFC 2119, March 1997."],
        ["[RFC8174]", "Leiba, B., \"Ambiguity of Uppercase vs Lowercase in RFC 2119 Key Words\", BCP 14, RFC 8174, May 2017."],
    ]))
    S("10.2", "Informative References")
    b.append(table(["Reference", "Document"], [
        ["[RFC7322]", "Flanagan, H. and S. Ginoza, \"RFC Style Guide\", RFC 7322, September 2014."],
        ["[IEEE754]", "IEEE, \"IEEE Standard for Floating-Point Arithmetic\", IEEE 754."],
        ["[DOCS]", "Space-Type, \"R-Type Documentation\", https://space-type.github.io/Documentation/."],
    ]))

    b.append(Block(["Authors' Addresses", ""], heading=("", "Authors' Addresses")))
    b.append(figure("""
        Space-Type team
        Epitech
        https://github.com/Space-Type
    """))
    return b


def main():
    blocks = abstract_blocks()
    content = body()
    first_page = front_matter()
    headings = [block.heading for block in content if block.heading]

    # The table of contents needs page numbers, which depend on its own length:
    # lay out once with placeholder numbers (same number of lines), then for real
    draft = Block(toc_block([(heading, 0) for heading in headings], 0))
    pages, found = paginate(blocks + [draft] + content, first_page)
    toc = Block(toc_block(found, 0))
    pages, final = paginate(blocks + [toc] + content, first_page)
    assert final == found, "the table of contents moved the sections"

    text = render(pages, first_page)
    for line in text.split("\n"):
        assert len(line) <= WIDTH, f"line too long: {line}"
    with open(OUTPUT, "w", encoding="ascii") as out:
        out.write(text)
    print(f"wrote {os.path.normpath(OUTPUT)}: {len(pages)} pages")


if __name__ == "__main__":
    main()
