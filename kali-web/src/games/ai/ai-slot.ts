import type { SlotIdValue } from "../core/constants/player-types";
import type { GameState } from "../core/types/game-state";
import type { GameAction } from "../core/types/game-action";
import { ActionType } from "../core/constants/action-types";
import type { WSClient } from "../../lib/wsClient";
import type { GameMoveResponseEvent } from "../../lib/protocol";
import { KaliError, fromGameMoveError } from "./kali-error";
import { KaliErrorCode, TttField } from "../core/constants/game-ai";

export class AISlot {
  private _abortController: AbortController | null = null;

  constructor(
    private _slotId: SlotIdValue,
    private _wsClient: WSClient | null = null,
  ) {}

  get slotId(): SlotIdValue {
    return this._slotId;
  }

  async decide(context: GameState): Promise<GameAction> {
    if (this._abortController) {
      this._abortController.abort();
    }
    this._abortController = new AbortController();

    if (!this._wsClient) {
      throw new KaliError(
        KaliErrorCode.WS_NULL,
        "No WebSocket connection available",
      );
    }

    const data = context.data as Record<string, unknown>;

    let response: GameMoveResponseEvent;
    try {
      response = await this._wsClient.sendAndWait<GameMoveResponseEvent>(
        {
          event: "game_move",
          game_type: "tictactoe",
          rules: {
            system_prompt: this._buildSystemPrompt(data),
            response_format: "json",
          },
          game_state: data,
          player_role: this._slotId,
          difficulty: data[TttField.DIFFICULTY] as string | undefined,
          starter: data[TttField.STARTER] as string | undefined,
          player_marker: data[TttField.PLAYER_MARK] as string | undefined,
          opponent_marker: data[TttField.OPPONENT_MARK] as string | undefined,
        },
        "game_move_response",
        undefined,
        this._abortController.signal,
      );
    } catch (err) {
      if (err instanceof Error && err.message.includes("timed out")) {
        throw new KaliError(
          KaliErrorCode.WS_TIMEOUT,
          "Kali no pudo responder a tiempo. La conexion se perdio o el servidor no respondio.",
        );
      }
      if (err instanceof Error && err.message.includes("aborted")) {
        console.info("[AISlot] request aborted — likely a new game started");
        throw new KaliError(
          KaliErrorCode.WS_ERROR,
          "Pedido anterior fue cancelado por un nuevo juego.",
        );
      }
      console.error("[AISlot] sendAndWait error:", err);
      throw new KaliError(
        KaliErrorCode.WS_ERROR,
        err instanceof Error ? err.message : String(err),
      );
    }

    if (response.error) {
      throw fromGameMoveError(
        response.error.code,
        response.error.message,
        response.error.fallback_action,
      );
    }

    if (response.action) {
      return {
        type: response.action.type as (typeof ActionType)[keyof typeof ActionType],
        data: response.action.data,
      };
    }

    throw new KaliError(
      KaliErrorCode.NO_LEGAL_MOVES,
      "No hay movimientos disponibles. El tablero esta lleno.",
    );
  }

  private _buildSystemPrompt(data: Record<string, unknown>): string {
    const difficulty = (data[TttField.DIFFICULTY] as string) ?? "medium";
    const opponentMarker = (data[TttField.OPPONENT_MARK] as string) ?? "O";
    const playerMarker = (data[TttField.PLAYER_MARK] as string) ?? "X";
    const starter = data[TttField.STARTER] as string;

    const instructions: Record<string, string> = {
      easy: "You are a beginner. Make random but reasonable moves.",
      medium: "Try to win. Block opponent's winning moves when possible.",
      hard: "Play optimally using minimax strategy. Take winning moves immediately.",
    };
    const instruction = instructions[difficulty] ?? instructions.medium;

    const board = data[TttField.BOARD] as (string | null)[][];
    const boardStr = board
      .map((row) => row.map((cell) => cell ?? "_").join(" | "))
      .map((line, r) => `row ${r}: ${line}`)
      .join("\n");

    return [
      "You are playing Tic-Tac-Toe.",
      `Your marker is ${opponentMarker}, opponent is ${playerMarker}.`,
      starter === "opponent" ? "You go first." : "Opponent (X) goes first.",
      instruction,
      `Current board (row 0-2, col 0-2):`,
      boardStr,
      "Output ONLY valid JSON with the row (0-2) and column (0-2) of your move.",
      '{"row": <number>, "col": <number>}',
    ].join("\n");
  }
}
