//! Source code written by Dmitry Ryzhenkov (https://github.com/cuicuidev)
//! Licenced under MIT Licence

const std = @import("std");
const mem = std.mem;
const fs = std.fs;

/// The type of the token
pub const TokenType = enum {
    INT,
    FLOAT,
    STRING,
    COL_SEP,
    ROW_SEP,
};

/// This struct holds the token
pub const Token = struct {
    allocator: mem.Allocator,
    value: []const u8,
    token_type: TokenType,

    const Self = @This();

    pub fn init(allocator: mem.Allocator, value: []const u8, token_type: TokenType) !Self {
        const val = try allocator.alloc(u8, value.len);
        mem.copyForwards(u8, val, value);
        return .{ .allocator = allocator, .value = val, .token_type = token_type };
    }

    pub fn deinit(self: *const Self) void {
        self.allocator.free(self.value);
    }

    pub fn printRepr(self: *Self, writer: fs.File.Writer) !void {
        try writer.print("Token{{ .value=\"", .{});
        for (self.value) |c| {
            if (c == '\n') {
                try writer.writeAll("\\n");
            } else {
                try writer.print("{c}", .{c});
            }
        }
        try writer.print("\", .token_type = {} }}\n", .{self.token_type});
    }
};

const Crawler = struct {
    start: usize,
    end: usize,

    const Self = @This();

    pub fn init() Self {
        return .{ .start = 0, .end = 0 };
    }

    pub fn crawl(self: *Self) void {
        self.end += 1;
    }

    pub fn pull(self: *Self) void {
        self.start = self.end;
    }

    pub fn drop(self: *Self) void {
        self.start = 0;
        self.end = 0;
    }
};

const State = enum { INT, FLOAT, STRING, QUOTED_STRING, COL_SEP, ROW_SEP, NEW_TOKEN, COMPLETE_TOKEN };

/// Config struct that holds the column separator character, the row separator character and the quotes character.
pub const CsvConfig = struct { col_sep: u8, row_sep: u8, quotes: u8 };

/// Reads a file and tokenizes the contents following the CsvConfig rules.
/// CsvConfig must be comptime known value.
/// Does not currently support lazy loading, so the buffer size must be big enough to hold the entire csv in memory.
pub fn CsvTokenizer(comptime config: CsvConfig) type {
    //TODO: Implement carryover from one buffer to the next, so that the tokens do not end up breaking.
    return struct {
        allocator: mem.Allocator,
        reader: fs.File.Reader,
        buffer: []u8,
        bytes_read: usize,
        carryover_buffer: std.ArrayList(u8),
        crawler: Crawler,
        tokens: std.ArrayList(Token),
        state: State,

        const Self = @This();

        /// Constructor.
        /// Takes a ptr to an allocator, a reader and a buffer size as arguments.
        pub fn init(allocator: mem.Allocator, reader: fs.File.Reader, buffer_size: usize) !Self {
            const buffer = allocator.alloc(u8, buffer_size) catch @panic("Unable to allocate buffer");
            const bytes_read = try reader.read(buffer);
            return .{
                .allocator = allocator,
                .reader = reader,
                .buffer = buffer,
                .bytes_read = bytes_read,
                .carryover_buffer = std.ArrayList(u8).init(allocator),
                .crawler = Crawler.init(),
                .tokens = std.ArrayList(Token).init(allocator),
                .state = State.NEW_TOKEN,
            };
        }

        /// Destructor.
        /// Deinits all dynamic structs and frees the buffer.
        pub fn deinit(self: *Self) void {
            self.allocator.free(self.buffer);
            self.carryover_buffer.deinit();
            for (self.tokens.items) |*token| {
                token.deinit();
            }
            self.tokens.deinit();
        }

        /// Takes a writer and prints each one of the tokens using the printRepr interface
        pub fn printTokens(self: *Self, writer: fs.File.Writer) !void {
            for (self.tokens.items) |*t| {
                try t.*.printRepr(writer);
            }
        }

        /// Tokenizes the whole file and stores all the tokens in the .tokens attribute
        pub fn tokenize(self: *Self) !void {
            while (true) {
                // std.debug.print("Bytes read: {}\t", .{self.bytes_read});
                // std.debug.print("N tokens: {}\n", .{self.tokens.items.len});
                if (self.bytes_read == 0) break;
                try self.tokenizeBuffer();
            }
        }

        /// Iterator interface to get the tokens one by one
        pub fn next(self: *Self) !?Token {
            while (true) {
                if (self.bytes_read == 0) return null;
                return self.nextToken() catch |err| {
                    switch (err) {
                        error.BufferReset => continue,
                        else => return err,
                    }
                };
            }
        }

        fn tokenizeBuffer(self: *Self) !void {
            while (self.crawler.end < self.bytes_read) {
                try self.nextChar();
            } else {
                // std.debug.print("BUFFER END\n", .{});
                try self.carryover_buffer.appendSlice(self.buffer[self.crawler.start..self.crawler.end]);
                self.bytes_read = try self.reader.read(self.buffer);
                self.crawler.drop();
            }
        }

        fn nextToken(self: *Self) !?Token {
            while (self.crawler.end < self.bytes_read) {
                try self.nextChar();
                if (self.state == State.COMPLETE_TOKEN) {
                    return self.tokens.pop();
                } else {
                    continue;
                }
            } else {
                // std.debug.print("BUFFER END\n", .{});
                try self.carryover_buffer.appendSlice(self.buffer[self.crawler.start..self.crawler.end]);
                self.bytes_read = try self.reader.read(self.buffer);
                self.crawler.drop();
                return error.BufferReset;
            }
            return null;
        }

        fn nextChar(self: *Self) !void {
            const char: u8 = self.buffer[self.crawler.end];
            switch (self.state) {
                State.NEW_TOKEN => self.stateNewToken(char),
                State.INT => try self.stateInt(char),
                State.FLOAT => try self.stateFloat(char),
                State.STRING => try self.stateString(char),
                State.QUOTED_STRING => try self.stateQuotedString(char),
                State.COL_SEP => try self.stateComma(),
                State.ROW_SEP => try self.stateLineBreak(),
                State.COMPLETE_TOKEN => self.stateCompleteToken(),
            }
        }

        fn stateNewToken(self: *Self, char: u8) void {
            switch (char) {
                '0'...'9' => self.state = State.INT,
                config.col_sep => self.state = State.COL_SEP,
                config.row_sep => self.state = State.ROW_SEP,
                config.quotes => {
                    self.state = State.QUOTED_STRING;
                    self.crawler.crawl();
                    self.crawler.pull();
                },
                '.' => self.state = State.FLOAT,
                else => self.state = State.STRING,
            }
        }

        fn stateInt(self: *Self, char: u8) !void {
            switch (char) {
                '0'...'9' => self.crawler.crawl(),
                '.' => self.state = State.FLOAT,
                config.col_sep, config.row_sep => try self.addToken(TokenType.INT),
                else => self.state = State.STRING,
            }
        }

        fn stateFloat(self: *Self, char: u8) !void {
            switch (char) {
                '0'...'9' => self.crawler.crawl(),
                config.col_sep, config.row_sep => try self.addToken(TokenType.FLOAT),
                else => self.state = State.STRING,
            }
        }

        fn stateString(self: *Self, char: u8) !void {
            switch (char) {
                config.col_sep, config.row_sep => try self.addToken(TokenType.STRING),
                else => self.crawler.crawl(),
            }
        }

        fn stateQuotedString(self: *Self, char: u8) !void {
            switch (char) {
                config.quotes => {
                    try self.addToken(TokenType.STRING);
                    self.crawler.crawl();
                },
                else => self.crawler.crawl(),
            }
        }

        fn stateComma(self: *Self) !void {
            self.crawler.crawl();
            try self.addToken(TokenType.COL_SEP);
        }

        fn stateLineBreak(self: *Self) !void {
            self.crawler.crawl();
            try self.addToken(TokenType.ROW_SEP);
        }

        fn stateCompleteToken(self: *Self) void {
            self.crawler.pull();
            self.state = State.NEW_TOKEN;
        }

        fn addToken(self: *Self, token_type: TokenType) !void {
            var slice: []u8 = undefined;
            const carryover_buffer_len = self.carryover_buffer.items.len;
            const token_len: usize = carryover_buffer_len + self.crawler.end - self.crawler.start;

            slice = try self.allocator.alloc(u8, token_len);
            defer self.allocator.free(slice);

            if (carryover_buffer_len > 0) {
                // std.debug.print("\nCarryover Len: {}\n", .{carryover_buffer_len});
                // std.debug.print("Crawler Len: {}\n", .{self.crawler.end - self.crawler.start});
                // std.debug.print("Token Len: {}\n\n", .{token_len});
                mem.copyForwards(u8, slice[0..carryover_buffer_len], self.carryover_buffer.items);
                self.carryover_buffer.clearAndFree();
            }

            mem.copyForwards(u8, slice[carryover_buffer_len..], self.buffer[self.crawler.start..self.crawler.end]);

            const token = try Token.init(self.allocator, slice, token_type);
            // const stdout = io.getStdOut().writer();
            // try token.printRepr(stdout);
            try self.tokens.append(token);
            self.state = State.COMPLETE_TOKEN;
        }
    };
}
