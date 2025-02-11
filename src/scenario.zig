const std = @import("std");

const mem = std.mem;
const fs = std.fs;
const csv = @import("csv.zig");

pub const ScenarioData = struct {
    allocator: mem.Allocator,
    scenario: []const u8,
    score: []const u8,
    challenge_start: []const u8,
    sens_scale: []const u8,
    sens_increment: []const u8,
    dpi: []const u8,
    fov: []const u8,
    fov_scale: []const u8,

    const Self = @This();

    pub fn deinit(self: *Self) void {
        self.allocator.free(self.scenario);
        self.allocator.free(self.score);
        self.allocator.free(self.challenge_start);
        self.allocator.free(self.sens_scale);
        self.allocator.free(self.sens_increment);
        self.allocator.free(self.dpi);
        self.allocator.free(self.fov);
        self.allocator.free(self.fov_scale);
    }

    pub fn fromCsvFile(allocator: mem.Allocator, path: []const u8) !Self {
        var csv_file = try fs.cwd().openFile(path, .{});
        defer csv_file.close();

        const csv_config = csv.CsvConfig{ .col_sep = ',', .row_sep = '\n', .quotes = '"' };
        var tokenizer = try csv.CsvTokenizer(csv_config).init(allocator, csv_file.reader(), 512);
        defer tokenizer.deinit();

        var scenario: []u8 = undefined;
        var score: []u8 = undefined;
        var challenge_start: []u8 = undefined;
        var sens_scale: []u8 = undefined;
        var sens_increment: []u8 = undefined;
        var dpi: []u8 = undefined;
        var fov: []u8 = undefined;
        var fov_scale: []u8 = undefined;

        var next_stat: ?StatType = null;
        while (try tokenizer.next()) |*token| {
            defer token.deinit();

            const token_val = std.mem.trim(u8, token.value, " \t\r\n");
            switch (token.token_type) {
                csv.TokenType.INT, csv.TokenType.FLOAT, csv.TokenType.STRING => {
                    if (next_stat) |next| {
                        switch (next) {
                            .scenario => {
                                scenario = try allocator.alloc(u8, token_val.len);
                                @memcpy(scenario, token_val);
                                next_stat = null;
                            },
                            .score => {
                                score = try allocator.alloc(u8, token_val.len);
                                @memcpy(score, token_val);
                                next_stat = null;
                            },
                            .challenge_start => {
                                challenge_start = try allocator.alloc(u8, token_val.len);
                                @memcpy(challenge_start, token_val);
                                next_stat = null;
                            },
                            .sens_scale => {
                                sens_scale = try allocator.alloc(u8, token_val.len);
                                @memcpy(sens_scale, token_val);
                                next_stat = null;
                            },
                            .sens_increment => {
                                sens_increment = try allocator.alloc(u8, token_val.len);
                                @memcpy(sens_increment, token_val);
                                next_stat = null;
                            },
                            .dpi => {
                                dpi = try allocator.alloc(u8, token_val.len);
                                @memcpy(dpi, token_val);
                                next_stat = null;
                            },
                            .fov => {
                                fov = try allocator.alloc(u8, token_val.len);
                                @memcpy(fov, token_val);
                                next_stat = null;
                            },
                            .fov_scale => {
                                fov_scale = try allocator.alloc(u8, token_val.len);
                                @memcpy(fov_scale, token_val);
                                next_stat = null;
                            },
                        }
                    } else {
                        if (mem.eql(u8, token_val, "Scenario:")) {
                            next_stat = StatType.scenario;
                        } else if (mem.eql(u8, token_val, "Score:")) {
                            next_stat = StatType.score;
                        } else if (mem.eql(u8, token_val, "Challenge Start:")) {
                            next_stat = StatType.challenge_start;
                        } else if (mem.eql(u8, token_val, "Sens Scale:")) {
                            next_stat = StatType.sens_scale;
                        } else if (mem.eql(u8, token_val, "Sens Increment:")) {
                            next_stat = StatType.sens_increment;
                        } else if (mem.eql(u8, token_val, "DPI:")) {
                            next_stat = StatType.dpi;
                        } else if (mem.eql(u8, token_val, "FOV:")) {
                            next_stat = StatType.fov;
                        } else if (mem.eql(u8, token_val, "FOVScale:")) {
                            next_stat = StatType.fov_scale;
                        }
                    }
                },
                else => {},
            }
        }

        return .{
            .allocator = allocator,
            .scenario = scenario,
            .score = score,
            .challenge_start = challenge_start,
            .sens_scale = sens_scale,
            .sens_increment = sens_increment,
            .dpi = dpi,
            .fov = fov,
            .fov_scale = fov_scale,
        };
    }

    pub fn print(self: *Self, writer: fs.File.Writer) !void {
        try writer.print("Scenario: {s}\n", .{self.scenario});
        try writer.print("Score: {s}\n", .{self.score});
        try writer.print("Challenge Start: {s}\n", .{self.challenge_start});
        try writer.print("Sens Scale: {s}\n", .{self.sens_scale});
        try writer.print("Sens Increment: {s}\n", .{self.sens_increment});
        try writer.print("DPI: {s}\n", .{self.dpi});
        try writer.print("FOV: {s}\n", .{self.fov});
        try writer.print("FOV Scale: {s}\n**************************************************\n\n", .{self.fov_scale});
    }

    pub fn jsonSerialize(self: *Self) ![]u8 {
        const fmt = "{{\"scenario\":\"{s}\",\"score\":{s},\"challenge_start\":\"{s}\",\"sens_scale\":\"{s}\",\"sens_increment\":{s},\"dpi\":{s},\"fov_scale\":\"{s}\",\"fov\":{s}}}";
        const json = try std.fmt.allocPrint(self.allocator, fmt, .{
            self.scenario,
            self.score,
            self.challenge_start,
            self.sens_scale,
            self.sens_increment,
            self.dpi,
            self.fov_scale,
            self.fov,
        });
        return json;
    }
};

const StatType = enum {
    scenario,
    score,
    challenge_start,
    sens_scale,
    sens_increment,
    dpi,
    fov,
    fov_scale,
};
