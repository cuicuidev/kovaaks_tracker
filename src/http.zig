const std = @import("std");
const mem = std.mem;
const http = std.http;
const fs = std.fs;

const scenario = @import("scenario.zig");

pub fn sendPayload(allocator: mem.Allocator, data: *scenario.ScenarioData, endpoint: []const u8, jwt: []const u8, writer: fs.File.Writer) !void {
    const payload = try data.jsonSerialize();
    defer allocator.free(payload);

    try writer.print("Sending scenario <{s}> | Score: {s}\n", .{ data.scenario, data.score });
    var client = http.Client{ .allocator = allocator };
    defer client.deinit();

    const uri = try std.Uri.parse(endpoint);

    var buf: [1024]u8 = undefined;
    var req = try client.open(.POST, uri, .{ .server_header_buffer = &buf });
    defer req.deinit();

    var auth_header_buffer: [256]u8 = undefined;
    const auth_header_slice = try std.fmt.bufPrint(&auth_header_buffer, "Bearer {s}", .{jwt});
    req.headers.authorization = http.Client.Request.Headers.Value{ .override = auth_header_slice };

    req.transfer_encoding = .{ .content_length = payload.len };
    try req.send();
    var wtr = req.writer();
    try wtr.writeAll(payload);
    try req.finish();
    try req.wait();

    var rdr = req.reader();
    const body = try rdr.readAllAlloc(allocator, 1024 * 1024 * 4);
    defer allocator.free(body);

    switch (req.response.status) {
        .ok => try writer.print("{} | Scenario <{s}> sent successfully\n\n", .{ req.response.status, data.scenario }),
        else => try writer.print("Error: <{}>\n\n", .{req.response.status}),
    }
}

pub fn getLatest(allocator: mem.Allocator, endpoint: []const u8, jwt: []const u8, writer: fs.File.Writer) !i128 {
    var client = http.Client{ .allocator = allocator };
    defer client.deinit();

    const uri = try std.Uri.parse(endpoint);

    var buf: [1024]u8 = undefined;
    var req = try client.open(.GET, uri, .{ .server_header_buffer = &buf });
    defer req.deinit();

    var auth_header_buffer: [256]u8 = undefined;
    const auth_header_slice = try std.fmt.bufPrint(&auth_header_buffer, "Bearer {s}", .{jwt});
    req.headers.authorization = http.Client.Request.Headers.Value{ .override = auth_header_slice };

    try req.send();
    try req.finish();
    try req.wait();

    var rdr = req.reader();
    const body = try rdr.readAllAlloc(allocator, 1024 * 1024 * 4);
    defer allocator.free(body);
    try writer.print("Latest timestamp: {s}\n\n", .{body});
    return std.fmt.parseInt(i128, body, 10);
}
