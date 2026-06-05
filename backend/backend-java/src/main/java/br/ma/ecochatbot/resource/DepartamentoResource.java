/*
 * EcoChatBot MA — Sistema de Atendimento Digital com IA
 * Autor  : Aldemir Queiroz
 * Início : 29/09/2025
 * Stack  : Java 17 + Quarkus 3.9 · Angular 17 (frontend: Diego Queiroz)
 *
 * Backend: DESENVOLVE APIs REST consumidas pelo frontend e por integrações
 * externas (WhatsApp Business / Evolution API · DeepSeek AI).
 */
package br.ma.ecochatbot.resource;

import br.ma.ecochatbot.dto.DepartamentoDTO;
import br.ma.ecochatbot.entity.Departamento;
import br.ma.ecochatbot.service.DepartamentoService;
import jakarta.inject.Inject;
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;

import java.util.List;

/**
 * API REST de Departamentos — expõe os endpoints HTTP consumidos pelo Angular (Diego).
 *
 * Padrão REST implementado:
 *   GET    /api/departamentos        → lista todos
 *   GET    /api/departamentos/{id}   → busca por ID (404 se não existe)
 *   POST   /api/departamentos        → cria novo (201 Created)
 *   PUT    /api/departamentos/{id}   → atualiza (404 se não existe)
 *   DELETE /api/departamentos/{id}   → remove (204 No Content ou 404)
 *
 * O Resource é apenas a camada HTTP — toda regra de negócio está no Service.
 */
@Path("/api/departamentos")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
public class DepartamentoResource {

    @Inject
    DepartamentoService service;

    @GET
    public List<Departamento> listar() {
        return service.listar();
    }

    @GET
    @Path("/{id}")
    public Response buscarPorId(@PathParam("id") Long id) {
        return service.buscarPorId(id)
            .map(d -> Response.ok(d).build())
            // Retorna 404 com mensagem — padrão para APIs REST bem documentadas
            .orElse(Response.status(Response.Status.NOT_FOUND)
                .entity("Departamento não encontrado: " + id).build());
    }

    @POST
    public Response criar(DepartamentoDTO dto) {
        Departamento criado = service.criar(dto);
        // 201 Created é o status correto para criação de recurso
        return Response.status(Response.Status.CREATED).entity(criado).build();
    }

    @PUT
    @Path("/{id}")
    public Response atualizar(@PathParam("id") Long id, DepartamentoDTO dto) {
        return service.atualizar(id, dto)
            .map(d -> Response.ok(d).build())
            .orElse(Response.status(Response.Status.NOT_FOUND)
                .entity("Departamento não encontrado: " + id).build());
    }

    @DELETE
    @Path("/{id}")
    public Response deletar(@PathParam("id") Long id) {
        boolean removido = service.deletar(id);
        if (removido) {
            // 204 No Content — DELETE bem-sucedido sem corpo de resposta
            return Response.noContent().build();
        }
        return Response.status(Response.Status.NOT_FOUND)
            .entity("Departamento não encontrado: " + id).build();
    }
}
